#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS — TIMELINE BUILDER v10.0
PD-Locked Broadcast Executor

Purpose
-------
Build the final episode timeline from:
- dialogue blocks
- episode context
- PD packets

This file does NOT route anchors.
PD is the final authority.

Design
------
• PD-locked anchor execution
• clean broadcast transitions
• preserves show shape
• additive OpenClaw hook support
• compatible with current ToknNews output contract

Author: TOKN Systems
"""

from __future__ import annotations

import json
import time
import re
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List

try:
    import openai
    OPENAI_ENABLED = True
except Exception:
    openai = None
    OPENAI_ENABLED = False

# global fallback toggle (ENV controlled)
FORCE_FALLBACK = os.getenv("TOKN_DISABLE_LLM", "0") == "1"

if OPENAI_ENABLED:
    openai.api_key = os.getenv("OPENAI_API_KEY")

from backend.script_engine.editorial.episode_context_builder import build_episode_context
from backend.script_engine.persona.pd_engine_v45 import pd_engine

openai.api_key = os.getenv("OPENAI_API_KEY")

INPUT_PATH = Path("/opt/toknnews/data/stories/dialogue_blocks.json")
OUTPUT_PATH = Path("/opt/toknnews/data/episodes/episode_timeline.json")
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

ARTIFACT_NUMERIC = Path("/opt/toknnews/data/artifacts/latest/numeric_context.json")

CHIP_MODEL = os.getenv("TOKN_CHIP_MODEL", "gpt-4.1-mini")

SECONDS_PER_TURN = float(os.getenv("TOKN_SECONDS_PER_TURN", "7.5"))
SECONDS_PER_MONOLOGUE = float(os.getenv("TOKN_SECONDS_PER_MONOLOGUE", "11"))
SECONDS_PER_TRANSITION = float(os.getenv("TOKN_SECONDS_PER_TRANSITION", "8"))

TARGET_RUNTIME_SEC = int(os.getenv("TOKN_TARGET_RUNTIME_SEC", "600"))
MIN_RUNTIME_SEC = int(os.getenv("TOKN_MIN_RUNTIME_SEC", "520"))


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _emit_openclaw_event(event_type: str, payload: Dict[str, Any]) -> None:
    if os.getenv("TOKN_OPENCLAW_HOOK") == "1":
        print(f"[OPENCLAW] {event_type} :: {json.dumps(payload)[:400]}")


def _domain(block: Dict[str, Any]) -> str:
    return clean(block.get("domain") or "general").lower()


def _thread_id(block: Dict[str, Any]) -> str:
    return clean(_safe_dict(block.get("showrunner_meta")).get("block_thread_id"))


def _segment_type(block: Dict[str, Any]) -> str:
    return clean(_safe_dict(block.get("pd_hints")).get("segment_type") or "support").lower()


def _timeline_item_runtime(item: Dict[str, Any]) -> int:
    item_type = clean(item.get("type"))

    if item_type == "dialogue":
        return int(item.get("runtime_sec") or 0)

    if item_type == "monologue":
        return int(SECONDS_PER_MONOLOGUE)

    if item_type == "transition":
        return int(SECONDS_PER_TRANSITION)

    return 0


def _estimate_timeline_runtime(timeline: List[Dict[str, Any]]) -> int:
    return int(sum(_timeline_item_runtime(item) for item in timeline))


# ---------------------------------------------------
# TTS SANITATION
# ---------------------------------------------------

PHONETIC_MAP = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "BNB": "Binance Coin",
    "XRP": "X R P",
    "ETF": "E T F",
    "AI": "A I",
}
TICKER_PATTERN = re.compile(r"\$(?:[A-Z]{2,6})\b")


def sanitize_tts(text: str) -> str:
    if not text or not isinstance(text, str):
        return ""

    out = text

    for k, v in PHONETIC_MAP.items():
        out = re.sub(rf"\b{re.escape(k)}\b", v, out)

    out = TICKER_PATTERN.sub("", out)
    out = re.sub(r"\s{2,}", " ", out).strip()
    return out


# ---------------------------------------------------
# NUMERIC CONTEXT
# ---------------------------------------------------

def _load_numeric_context() -> Dict[str, Any]:
    if not ARTIFACT_NUMERIC.exists():
        return {}

    try:
        data = json.loads(ARTIFACT_NUMERIC.read_text())
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _numeric_one_liner(numeric: Dict[str, Any]) -> str:
    if not numeric:
        return ""

    chains = _safe_dict(numeric.get("chains"))
    eth = _safe_dict(chains.get("ethereum"))
    price = _safe_dict(eth.get("price")).get("usd")

    if isinstance(price, (int, float)):
        return f"Ethereum is near ${price:,.0f}."

    return ""


# ---------------------------------------------------
# NAME HELPERS
# ---------------------------------------------------

def _anchor_toss_name(anchor: str) -> str:
    name = clean(anchor).lower()
    return {
        "cash": "Cash",
        "bond": "Bond",
        "ledger": "Ledger",
        "reef": "Reef",
        "lawson": "Lawson",
        "neura": "Neura",
        "bitsy": "Bitsy",
        "penny": "Penny",
        "ivy": "Ivy",
        "chip": "Chip",
        "vega": "Vega",
    }.get(name, name.capitalize() if name else "Chip")


def _brief_title(block: Dict[str, Any]) -> str:
    thesis = clean(block.get("thesis"))
    implication = clean(block.get("implication"))
    seed = thesis or implication or clean(block.get("domain")) or "the story"
    words = seed.split()
    return sanitize_tts(" ".join(words[:10]))


# ---------------------------------------------------
# OPEN / CLOSE
# ---------------------------------------------------

def vega_intro() -> Dict[str, Any]:
    return {
        "type": "monologue",
        "speaker": "vega",
        "text": "Welcome to Token News. The world’s first fully autonomous A I broadcast. Here’s your host, Chip Blue.",
        "ts": time.time(),
    }


def generate_chip_open_monologue(first_block: Dict[str, Any], episode_ctx: Dict[str, Any], numeric: Dict[str, Any]) -> Dict[str, Any]:
    hour = datetime.utcnow().hour

    if 5 <= hour < 12:
        daypart = "This morning"
    elif 12 <= hour < 17:
        daypart = "This afternoon"
    else:
        daypart = "Tonight"

    thesis = clean(episode_ctx.get("episode_thesis") or "the market story is mixed")
    signal_summary = clean(episode_ctx.get("signal_summary"))
    num_line = _numeric_one_liner(numeric)

    fallback = f"{daypart}, Token News is tracking {thesis}."
    if num_line:
        fallback = f"{fallback} {num_line}"

    if not OPENAI_ENABLED or FORCE_FALLBACK:
        return {"type": "monologue", "speaker": "chip", "text": sanitize_tts(fallback), "ts": time.time()}

    try:
        prompt = f"""
You are Chip, lead anchor of Token News.

Write ONE opening line.

Use:
- daypart: {daypart}
- thesis: {thesis}
- signal summary: {signal_summary}
- numeric line: {num_line}

Rules:
- 18 to 30 words
- one sentence
- calm authority
- no hype

Return ONLY the sentence.
""".strip()

        rsp = openai.ChatCompletion.create(
            model=CHIP_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.35,
            max_tokens=70,
            request_timeout=10,
        )

        text = sanitize_tts(rsp["choices"][0]["message"]["content"].strip())

        return {"type": "monologue", "speaker": "chip", "text": text, "ts": time.time()}

    except Exception:
        return {"type": "monologue", "speaker": "chip", "text": sanitize_tts(fallback), "ts": time.time()}

def generate_chip_outro(episode_ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    TOKNNEWS — CHIP + VEGA OUTRO (2-PART BROADCAST CLOSE)

    Structure
    ---------
    1. Chip → narrative close (analysis wrap)
    2. Vega → brand + CTA (broadcast identity)

    Safe:
    - fully guarded OpenAI calls
    - fallback if model unavailable
    """

    thesis = clean(episode_ctx.get("episode_thesis") or "the market story remains mixed")
    signal_summary = clean(episode_ctx.get("signal_summary") or "")
    risk_direction = clean(episode_ctx.get("risk_direction") or "mixed")

    timeline_out: List[Dict[str, Any]] = []

    # ---------------------------------------------------
    # CHIP — NARRATIVE CLOSE
    # ---------------------------------------------------

    chip_fallback = "Tonight’s story was rotation, pressure, and whether flows truly confirm price."

    chip_text = chip_fallback

    if OPENAI_ENABLED:
        try:
            prompt = f"""
You are Chip closing Token News.

Write ONE clean closing line.

Context:
- Thesis: {thesis}
- Signals: {signal_summary}
- Risk: {risk_direction}

Rules:
- 10 to 20 words
- one sentence
- calm, authoritative
- no hype
- no CTA
- no thank you

Return ONLY the sentence.
""".strip()

            rsp = openai.ChatCompletion.create(
                model=CHIP_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.35,
                max_tokens=45,
                request_timeout=10,
            )

            content = rsp["choices"][0]["message"]["content"]
            if isinstance(content, str) and content.strip():
                chip_text = sanitize_tts(content.strip())

        except Exception:
            chip_text = sanitize_tts(chip_fallback)

    else:
        chip_text = sanitize_tts(chip_fallback)

    timeline_out.append({
        "type": "monologue",
        "speaker": "chip",
        "text": chip_text,
        "ts": time.time(),
    })

    # ---------------------------------------------------
    # VEGA — BRAND + CTA CLOSE
    # ---------------------------------------------------

    vega_text = "Thanks for watching Token News. Stay ahead of the signal — we’ll see you next cycle."

    timeline_out.append({
        "type": "monologue",
        "speaker": "vega",
        "text": sanitize_tts(vega_text),
        "ts": time.time(),
    })

    return timeline_out

# ---------------------------------------------------
# PD-LOCKED TRANSITIONS
# ---------------------------------------------------

def generate_transition(prev_packet: Dict[str, Any], next_packet: Dict[str, Any]) -> Dict[str, Any]:
    next_story = _safe_dict(next_packet.get("story"))
    next_anchor = clean(next_packet.get("primary") or "chip")
    anchor_name = _anchor_toss_name(next_anchor)
    title = _brief_title(next_story)

    text = f"{anchor_name} — walk us through {title}."

    return {
        "type": "transition",
        "speaker": "chip",
        "text": sanitize_tts(text),
        "ts": time.time(),
    }


# ---------------------------------------------------
# PD-LOCKED DIALOGUE
# ---------------------------------------------------

def build_dialogue_from_packet(packet: Dict[str, Any]) -> tuple[list[Dict[str, str]], list[str]]:
    story = _safe_dict(packet.get("story"))
    raw_turns = _safe_list(story.get("dialogue"))

    anchors = [
        clean(a).lower()
        for a in _safe_list(packet.get("anchors"))
        if clean(a)
    ]

    if not anchors:
        anchors = ["chip"]

    turns_out: List[Dict[str, str]] = []

    for idx, turn in enumerate(raw_turns):
        turn = _safe_dict(turn)
        text = sanitize_tts(clean(turn.get("text")))
        if not text:
            continue

        explicit_speaker = clean(turn.get("speaker")).lower()

        if explicit_speaker:
            speaker = explicit_speaker
        else:
            speaker = anchors[idx % len(anchors)]

        turns_out.append({
            "speaker": speaker,
            "text": text,
        })

    if not turns_out:
        implication = sanitize_tts(clean(story.get("implication") or story.get("thesis")))
        if implication:
            turns_out.append({
                "speaker": anchors[0],
                "text": implication,
            })

    return turns_out, anchors


# ---------------------------------------------------
# ORDERING
# ---------------------------------------------------

def _packet_sort_key(packet: Dict[str, Any]) -> tuple:
    segment_type = clean(packet.get("segment_type") or "support").lower()
    weight = {"lead": 0, "support": 1, "filler": 2}.get(segment_type, 1)
    heat = _safe_float(packet.get("heat"), 0.0)
    return (weight, -heat)


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

def build_timeline(blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    _emit_openclaw_event("timeline_start", {"blocks": len(blocks)})

    episode_ctx = build_episode_context(blocks)
    numeric = _load_numeric_context()

    show_mode = os.getenv("TOKN_SHOW_MODE", "NEWS")
    latenight = show_mode == "CHAOS"

    pd_packets = pd_engine(blocks, mode=show_mode, latenight=latenight)
    pd_packets.sort(key=_packet_sort_key)

    timeline: List[Dict[str, Any]] = []

    if not pd_packets:
        timeline.append(vega_intro())
        timeline.append({
            "type": "monologue",
            "speaker": "chip",
            "text": "Token News is live. We’ll be back with a full rundown shortly.",
            "ts": time.time(),
        })
        timeline.extend(generate_chip_outro(episode_ctx))
        return timeline

    first_story = _safe_dict(pd_packets[0].get("story"))

    timeline.append(vega_intro())
    timeline.append(generate_chip_open_monologue(first_story, episode_ctx, numeric))

    prev_packet: Dict[str, Any] | None = None

    for packet in pd_packets:
        story = _safe_dict(packet.get("story"))
        segment_id = clean(story.get("narrative_id"))

        _emit_openclaw_event("segment_start", {
            "segment_id": segment_id,
            "primary": packet.get("primary"),
            "anchors": packet.get("anchors"),
        })

        if prev_packet is not None:
            timeline.append(generate_transition(prev_packet, packet))

        turns_out, anchors = build_dialogue_from_packet(packet)

        if not turns_out:
            continue

        runtime_sec = int(packet.get("runtime_suggested_sec") or max(20, int(len(turns_out) * SECONDS_PER_TURN)))

        timeline.append({
            "type": "dialogue",
            "segment_id": segment_id,
            "domain": _domain(story),
            "anchors": anchors,
            "primary": clean(packet.get("primary")),
            "secondary": clean(packet.get("secondary")),
            "tertiary": clean(packet.get("tertiary")),
            "turns": turns_out,
            "runtime_sec": runtime_sec,
            "energy_level": packet.get("energy_level"),
            "ts": time.time(),
            "thread_id": _thread_id(story),
            "segment_type": clean(packet.get("segment_type") or _segment_type(story) or "support"),
            "pd_packet": {
                "primary": clean(packet.get("primary")),
                "secondary": clean(packet.get("secondary")),
                "tertiary": clean(packet.get("tertiary")),
                "anchors": anchors,
                "runtime_suggested_sec": runtime_sec,
                "energy_level": packet.get("energy_level"),
            },
        })

        prev_packet = packet

        _emit_openclaw_event("segment_complete", {
            "segment_id": segment_id,
            "runtime_sec": runtime_sec,
        })

        if _estimate_timeline_runtime(timeline) >= TARGET_RUNTIME_SEC:
            break

    if _estimate_timeline_runtime(timeline) < MIN_RUNTIME_SEC:
        last_packet = prev_packet
        if last_packet is not None:
            story = _safe_dict(last_packet.get("story"))
            primary = _anchor_toss_name(clean(last_packet.get("primary") or "chip"))
            timeline.append({
                "type": "transition",
                "speaker": "chip",
                "text": sanitize_tts(f"{primary} — what changes if that trend keeps building?"),
                "ts": time.time(),
            })

    timeline.append(generate_chip_outro(episode_ctx))

    _emit_openclaw_event("timeline_complete", {
        "items": len(timeline),
        "runtime_est": _estimate_timeline_runtime(timeline),
    })

    return timeline


# ---------------------------------------------------
# ENTRYPOINT
# ---------------------------------------------------

def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing dialogue_blocks.json")

    dialogue_blocks = json.loads(INPUT_PATH.read_text())
    timeline = build_timeline(dialogue_blocks)

    OUTPUT_PATH.write_text(json.dumps(timeline, indent=2))

    print(f"[TIMELINE] Wrote {len(timeline)} timeline blocks → {OUTPUT_PATH}")
    print(f"[TIMELINE] Estimated runtime ≈ {_estimate_timeline_runtime(timeline)}s")


if __name__ == "__main__":
    main()
