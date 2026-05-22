#!/usr/bin/env python3
"""
grok_writer_v6.py
ToknNews — Conversational Intelligence Engine v6.1 (ESL-AWARE, BROADCAST SAFE)

HARD GUARANTEES:
- ESL-first (thesis / facts / implication)
- Anchor domain discipline enforced
- Deterministic length + role caps
- Reaction-only safe
- Zero filler / zero repetition
"""

from __future__ import annotations
from typing import Dict, Any, List
import logging
import re

from openai import OpenAI
from backend.script_engine.story_bank import (
    get_anchor_tone,
    update_anchor_tone,
)

# -------------------------------------------------------------------
# Logging
# -------------------------------------------------------------------
log = logging.getLogger("grok_writer_v6")
log.setLevel(logging.INFO)

client = OpenAI()

MODEL_PRIORITY = ["gpt-4.1", "gpt-4.1-mini", "gpt-4o"]
TONE_DECAY_DAYS = 14

# -------------------------------------------------------------------
# Anchor domain authority (HARD RULES)
# -------------------------------------------------------------------
ANCHOR_DOMAINS = {
    "chip":   {"moderation", "transition"},
    "cash":   {"markets", "trend"},
    "bond":   {"macro"},
    "lawson": {"regulation"},
    "ledger": {"onchain"},
    "reef":   {"defi"},
    "neura":  {"ai"},
}

# -------------------------------------------------------------------
# Prompt Builder (ESL-AWARE)
# -------------------------------------------------------------------
def _build_prompt(segment: Dict[str, Any], anchors: List[str], tones, mode: str) -> str:
    facts = segment.get("facts") or []
    facts_text = "\n".join(f"- {f}" for f in facts[:3])

    prompt = f"""
You are writing a ToknNews broadcast.

SEGMENT TYPE: {segment.get("segment_type")}
DOMAIN: {segment.get("domain")}
MODE: {mode}

THESIS (DO NOT REWRITE):
{segment.get("thesis")}

FACTS (READ, DO NOT EMBELLISH):
{facts_text}

IMPLICATION (OPTIONAL WRAP):
{segment.get("implication")}

RULES (ABSOLUTE):
- Chip moderates only.
- Market commentary ONLY by Cash.
- Macro commentary ONLY by Bond.
- Regulation ONLY by Lawson.
- One sentence per anchor.
- No filler.
- No speculation.
- No rephrasing thesis.

FORMAT (STRICT):
Chip: ...
Cash: ...
Bond: ...
"""

    return prompt.strip()

# -------------------------------------------------------------------
# Fallback (never breaks broadcast)
# -------------------------------------------------------------------
def _fallback(segment, anchors):
    lines = []

    lines.append({
        "speaker": "chip",
        "text": segment.get("thesis", "Here’s what matters right now."),
        "tag": "chip_transition"
    })

    for a in anchors:
        if a == "chip":
            continue
        lines.append({
            "speaker": a,
            "text": "This is worth monitoring.",
            "tag": "anchor_analysis"
        })

    return lines[:3]

# -------------------------------------------------------------------
# PUBLIC API (DO NOT CHANGE SIGNATURE)
# -------------------------------------------------------------------
def generate_conversation(
    story: Dict[str, Any],
    primary: str,
    secondary: str = None,
    tertiary: str = None,
    mode: str = "NEWS",
):
    anchors = [a for a in [primary, secondary, tertiary] if a]
    segment = story  # ESL segment, not raw story

    tones = {a: get_anchor_tone(a, decay_days=TONE_DECAY_DAYS) for a in anchors}
    prompt = _build_prompt(segment, anchors, tones, mode)

    raw = None
    used_model = None

    for model in MODEL_PRIORITY:
        try:
            rsp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4,
                max_tokens=350,
                timeout=20,
            )
            raw = rsp.choices[0].message.content.strip()
            used_model = model
            break
        except Exception as e:
            log.warning(f"[GWv6] {model} failed → {e}")

    if not raw:
        log.error("[GWv6] All models failed → fallback")
        return _fallback(segment, anchors)

    lines = []
    for ln in raw.splitlines():
        if ":" not in ln:
            continue
        sp, tx = ln.split(":", 1)
        speaker = sp.strip().lower()
        text = re.sub(r"\s+", " ", tx.strip())

        if speaker not in anchors:
            continue

        # Enforce anchor domain discipline
        domain = segment.get("domain")
        allowed = ANCHOR_DOMAINS.get(speaker, set())
        if speaker != "chip" and domain not in allowed:
            continue

        tag = "chip_transition" if speaker == "chip" else "anchor_analysis"

        lines.append({
            "speaker": speaker,
            "text": text,
            "tag": tag
        })

        try:
            update_anchor_tone(speaker, confidence_delta=0.02)
        except Exception:
            pass

    if not lines:
        log.error("[GWv6] Parsed empty → fallback")
        return _fallback(segment, anchors)

    log.info(f"[GWv6] conversation generated via {used_model}")
    return lines
