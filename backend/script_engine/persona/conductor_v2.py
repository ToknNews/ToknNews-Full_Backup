#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝

TOKNNEWS PERSONA ENGINE – Conductor v3

Improvements over v2:
- Session-based OpenClaw calls for real conversational memory
- Simplified, personality-first prompts (no rule overload)
- Better role resolution and memory injection
- Optional parallelism for faster broadcasts
- TTS hook ready (commented – enable when TTS is set up)
- Keeps all your paths, fallbacks, sanitization, atomic writes

"""

from __future__ import annotations

import json
import os
import re
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------
# PATHS (unchanged)
# ---------------------------------------------------------

SHOW_DIRECTOR_PATH = Path("/opt/toknnews/data/show_director.json")
HOST_INTENTS_PATH = Path("/opt/toknnews/data/host_intents.json")
STORY_CONTEXT_PATH = Path("/opt/toknnews/data/story_context_packets.json")

OUTPUT_JSON_PATH = Path("/opt/toknnews/data/broadcast/broadcast_roundtable.json")
OUTPUT_TXT_PATH = Path("/opt/toknnews/data/broadcast/broadcast_roundtable.txt")
TMP_OUTPUT_JSON_PATH = OUTPUT_JSON_PATH.with_suffix(".tmp")

SHARED_MEMORY_DIR = Path("/opt/toknclaw/anchor_memory")
CAST_BIBLE_PATH = SHARED_MEMORY_DIR / "ANCHOR_CAST_BIBLE.md"
LAST_SHOW_SUMMARY_PATH = SHARED_MEMORY_DIR / "LAST_SHOW_SUMMARY.md"

# ---------------------------------------------------------
# ENV / RUNTIME (unchanged)
# ---------------------------------------------------------

TOKN_OPENCLAW_BIN = os.getenv("TOKN_OPENCLAW_BIN", "openclaw")
TOKN_CONDUCTOR_TIMEOUT_SEC = int(os.getenv("TOKN_CONDUCTOR_TIMEOUT_SEC", "25"))
TOKN_CONDUCTOR_CONTEXT_TURNS = int(os.getenv("TOKN_CONDUCTOR_CONTEXT_TURNS", "3"))
TOKN_DEBUG_CONDUCTOR = os.getenv("TOKN_DEBUG_CONDUCTOR", "0") == "1"
TOKN_PARALLEL_TURNS = int(os.getenv("TOKN_PARALLEL_TURNS", "4"))  # new: max concurrent agents

# ---------------------------------------------------------
# HELPERS (mostly unchanged)
# ---------------------------------------------------------

def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def now_ts() -> float:
    return time.time()


def atomic_write_json(path: Path, tmp_path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _debug(msg: str) -> None:
    if TOKN_DEBUG_CONDUCTOR:
        print(f"[CONDUCTOR v3] {msg}")


def sanitize_spoken_text(text: str) -> str:
    if not text:
        return ""

    out = str(text).strip()

    phonetic_map = {
        "BTC": "Bitcoin",
        "ETH": "Ethereum",
        "SOL": "Solana",
        "USDT": "U S D T",
        "USDC": "U S D C",
        "ETF": "E T F",
        "AI": "A I",
        "SP500": "S and P 500",
        "TVL": "T V L",
    }

    for src, dst in phonetic_map.items():
        out = re.sub(rf"\b{re.escape(src)}\b", dst, out)

    out = re.sub(r"\s+", " ", out).strip()
    return out


def load_json(path: Path) -> Any:
    if not path.exists():
        raise FileNotFoundError(f"Missing input file: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def optional_file_tail(path: Path, max_chars: int) -> str:
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8").strip()
    if len(text) <= max_chars:
        return text
    return text[-max_chars:]


# ---------------------------------------------------------
# OPENCLAW SESSION CALL (NEW – uses persistent sessions)
# ---------------------------------------------------------

def send_to_anchor(anchor_id: str, message: str) -> Tuple[str, Dict[str, Any]]:
    """Send message to anchor via persistent OpenClaw session"""
    cmd = [
        TOKN_OPENCLAW_BIN,
        "session", "send",
        f"agent:{anchor_id}",
        "--message", message,
        "--format", "text"
    ]

    _debug(f"Sending to {anchor_id}: {message[:80]}...")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TOKN_CONDUCTOR_TIMEOUT_SEC,
            check=False
        )
        if result.returncode != 0:
            return "", {"mode": "error", "stderr": result.stderr.strip()}
        return clean(result.stdout.strip()), {"mode": "ok"}
    except Exception as e:
        return "", {"mode": "error", "reason": str(e)}


# ---------------------------------------------------------
# STORY & INTENT HANDLING (mostly unchanged)
# ---------------------------------------------------------

def build_story_lookup(story_context_packets: Dict[str, Any]) -> List[Dict[str, Any]]:
    return safe_list(story_context_packets.get("stories"))


def build_story_cursor_state() -> Dict[str, Any]:
    return {"index": 0, "current_story": None}


def current_story_or_default(state: Dict[str, Any], stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    current = safe_dict(state.get("current_story"))
    if current:
        return current
    if stories:
        return safe_dict(stories[0])
    return {}


def advance_story(state: Dict[str, Any], stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    idx = int(state.get("index", 0))
    if idx >= len(stories):
        story = safe_dict(stories[-1]) if stories else {}
        state["current_story"] = story
        return story

    story = safe_dict(stories[idx])
    state["current_story"] = story
    state["index"] = idx + 1
    return story


def build_recent_turns_block(previous_turns: List[Dict[str, Any]]) -> str:
    if not previous_turns:
        return "No prior discussion."
    recent = previous_turns[-TOKN_CONDUCTOR_CONTEXT_TURNS:]
    lines = [f"{clean(turn.get('speaker', 'Unknown')).title()}: {clean(turn.get('text'))}" for turn in recent]
    return "Recent discussion:\n" + "\n".join(lines)


def build_memory_block() -> str:
    cast_bible = optional_file_tail(CAST_BIBLE_PATH, 600)
    last_show = optional_file_tail(LAST_SHOW_SUMMARY_PATH, 400)

    parts = []
    if cast_bible:
        parts.append(f"Cast dynamics (use for rapport):\n{cast_bible}")
    if last_show:
        parts.append(f"Recent narrative:\n{last_show}")

    if not parts:
        return ""
    combined = "\n\n".join(parts)
    return combined[:1000]  # hard safety clamp

def resolve_target_anchor(intent: Dict[str, Any], story: Dict[str, Any]) -> str:
    """
    Determine which anchor should respond based on intent or story roles.
    """
    explicit_target = clean(intent.get("target_anchor")).lower()
    if explicit_target:
        return explicit_target

    # Fallback: try to get from story metadata if present
    anchor_roles = safe_dict(story.get("anchor_roles"))
    lead = clean(anchor_roles.get("lead")).lower()
    counter = clean(anchor_roles.get("counter")).lower()

    intent_type = clean(intent.get("type"))

    if intent_type == "question":
        return lead or "bond"  # default to macro guy

    if intent_type == "challenge":
        return counter or "cash"  # default to retail

    if intent_type == "bitsy_toss":
        return "bitsy"

    return ""  # no specific target


def resolve_effective_speaker(intent: Dict[str, Any], story: Dict[str, Any]) -> str:
    """
    Decide who actually speaks in this turn (original speaker or targeted one).
    """
    base_speaker = clean(intent.get("speaker")).lower()
    intent_type = clean(intent.get("type"))

    # For interactive intents, use the target
    if intent_type in {"question", "challenge"}:
        target = resolve_target_anchor(intent, story)
        if target:
            return target

    # Otherwise fall back to whoever is listed as speaker
    return base_speaker or "chip"  # safety fallback to host

def build_story_block(story: Dict[str, Any]) -> str:
    story = safe_dict(story)
    if not story:
        return "No story available."

    parts = [
        f"Title: {clean(story.get('title'))}",
        f"Entity: {clean(story.get('resolved_entity') or story.get('entity'))}",
        f"Domain: {clean(story.get('domain'))}",
        f"Summary: {clean(story.get('summary'))}",
        f"Key takeaway: {clean(story.get('key_takeaway'))}",
        f"Debate angle: {clean(story.get('debate_angle'))}",
    ]
    raw_url = clean(story.get("raw_url"))
    if raw_url:
        parts.append(f"Source: {raw_url}")

    return "\n".join(parts)


# ---------------------------------------------------------
# SIMPLIFIED PROMPT – personality via SOUL.md, not here
# ---------------------------------------------------------
def build_prompt(
    intent: Dict[str, Any],
    story: Dict[str, Any],
    previous_turns: List[Dict[str, Any]],
    chip_profile: Dict[str, Any],
) -> str:

    speaker = clean(intent.get("speaker")).lower()
    intent_type = clean(intent.get("type"))

    story_block = build_story_block(story)
    recent = build_recent_turns_block(previous_turns)
    memory = build_memory_block()

    resolved_entity = clean(story.get("resolved_entity") or story.get("entity"))

    # ---------------------------------------------------------
    # ROLE HINT (LIGHT — NOT OVERPOWERING)
    # ---------------------------------------------------------

    role_hint = ""

    if speaker == "chip":
        if intent_type == "question":
            target = clean(intent.get("target_anchor")) or "bond"
            role_hint = f"{target.title()}, what actually matters here for {resolved_entity}?"

        elif intent_type == "transition":
            role_hint = "Move the conversation forward naturally."

        elif intent_type == "act_intro":
            role_hint = f"Set up the {clean(story.get('domain'))} segment."

        elif intent_type == "show_open":
            role_hint = "Open the show with authority."

        elif intent_type == "show_close":
            role_hint = "Close the show cleanly."

    else:
        # 🔥 THIS IS THE KEY FIX
        role_hint = f"Give your take on {resolved_entity}."

    prompt = f"""
You are {speaker} on ToknNews.

{role_hint}

CURRENT STORY
{story_block}

RECENT CONVERSATION
{recent}

CAST MEMORY
{memory}

Respond in 1–2 sentences. Speak naturally. Stay in character.
""".strip()

    return prompt

# ---------------------------------------------------------
# FALLBACKS (kept but tightened)
# ---------------------------------------------------------

def fallback_text(intent: Dict[str, Any], story: Dict[str, Any]) -> str:
    speaker = clean(intent.get("speaker")).lower()
    intent_type = clean(intent.get("type"))
    entity = clean(story.get("resolved_entity") or story.get("entity"))

    if speaker == "vega":
        return "Welcome to ToknNews.The worlds first fully autonomous A I Broadcast. Here's your host, Chip Blue!" if intent_type == "vega_intro" else "Thanks for watching ToknNews."

    if speaker == "chip":
        if intent_type == "show_open":
            return "Markets are moving — let's break down what actually matters tonight."
        if intent_type == "show_close":
            return "That's the board. We'll see which signals hold."

    if speaker == "bitsy":
        return "This market is straight clown shoes."

    return f"Yeah, {entity} is the one to watch right now."


# ---------------------------------------------------------
# EXECUTION – with optional parallelism
# ---------------------------------------------------------

def execute_turn(binding: Dict[str, Any], previous_turns: List[Dict[str, Any]], chip_profile: Dict[str, Any]) -> Dict[str, Any]:
    intent = safe_dict(binding.get("intent"))
    story = safe_dict(binding.get("story"))

    speaker = clean(intent.get("speaker")).lower()
    effective_speaker = resolve_effective_speaker(intent, story)  # your existing function

    prompt = build_prompt(intent, story, previous_turns, chip_profile)

    text, meta = send_to_anchor(effective_speaker, prompt)

    if not text:
        text = fallback_text(intent, story)

    text = sanitize_spoken_text(text)

    # Enforce brevity (soft – models should follow prompt now)
    sentences = re.split(r'[.!?]+', text)
    if len(sentences) > 2:
        text = ". ".join(sentences[:2]).strip() + "."

    words = text.split()
    if len(words) > 60:  # relaxed from 40
        text = " ".join(words[:60]).strip()

    if effective_speaker == "bitsy":
        words = text.split()
        if len(words) > 16:
            text = " ".join(words[:16]).rstrip(" ,.;:!?")

    return {
        "turn_index": len(previous_turns),
        "speaker": effective_speaker,
        "intent_type": clean(intent.get("type")),
        "text": text,
        "story_ref": {
            "title": clean(story.get("title")),
            "entity": clean(story.get("entity")),
            "resolved_entity": clean(story.get("resolved_entity")),
            "domain": clean(story.get("domain")),
        },
        "meta": meta,
    }

def build_intent_story_bindings(
    intents_payload: Dict[str, Any],
    stories_payload: Dict[str, Any],
) -> List[Dict[str, Any]]:
    intents = safe_list(intents_payload.get("intents"))
    stories = build_story_lookup(stories_payload)

    story_state = build_story_cursor_state()
    bindings: List[Dict[str, Any]] = []

    for intent in intents:
        intent = safe_dict(intent)
        intent_type = clean(intent.get("type"))

        if intent_type in {"question"}:
            story = advance_story(story_state, stories)
        elif intent_type in {"challenge", "bitsy_toss"}:
            story = current_story_or_default(story_state, stories)
        elif intent_type in {"act_intro", "transition"}:
            story = current_story_or_default(story_state, stories)
        elif intent_type in {"show_open", "show_close", "vega_intro", "vega_outro"}:
            story = current_story_or_default(story_state, stories)
        else:
            story = current_story_or_default(story_state, stories)

        bindings.append(
            {
                "intent": intent,
                "story": safe_dict(story),
            }
        )

    return bindings

def execute_roundtable(
    show_director: Dict[str, Any],
    host_intents: Dict[str, Any],
    story_context_packets: Dict[str, Any],
) -> Dict[str, Any]:
    chip_profile = safe_dict(host_intents.get("chip_profile"))
    bindings = build_intent_story_bindings(host_intents, story_context_packets)  # your existing function

    executed_turns: List[Dict[str, Any]] = []
    turn_log: List[Dict[str, Any]] = []

    # Optional parallelism (set TOKN_PARALLEL_TURNS=1 to disable)
    if TOKN_PARALLEL_TURNS > 1:
        with ThreadPoolExecutor(max_workers=TOKN_PARALLEL_TURNS) as executor:
            future_to_binding = {
                executor.submit(execute_turn, binding, executed_turns, chip_profile): binding
                for binding in bindings
            }
            for future in as_completed(future_to_binding):
                turn = future.result()
                executed_turns.append(turn)
                turn_log.append({"turn_index": turn["turn_index"], "meta": turn["meta"]})
    else:
        for binding in bindings:
            turn = execute_turn(binding, executed_turns, chip_profile)
            executed_turns.append(turn)
            turn_log.append({"turn_index": turn["turn_index"], "meta": turn["meta"]})

    text_export = "\n".join(
        f"{clean(turn.get('speaker', 'Unknown')).title()}: {clean(turn.get('text'))}"
        for turn in executed_turns
    )

    # Optional TTS placeholder (uncomment when ready)
    # for turn in executed_turns:
    #     speak_anchor(turn["text"], turn["speaker"], f"audio/{turn['turn_index']}.wav")

    return {
        "generated_at": now_ts(),
        "show_mode": "broadcast_roundtable",
        "turn_count": len(executed_turns),
        "timeline": executed_turns,
        "meta": {
            "show_flow": safe_dict(show_director.get("show_flow")),
            "context_turns": TOKN_CONDUCTOR_CONTEXT_TURNS,
            "timeout_sec": TOKN_CONDUCTOR_TIMEOUT_SEC,
            "parallel_workers": TOKN_PARALLEL_TURNS,
            "turn_log": turn_log,
        },
        "text_export": text_export,
    }


# ---------------------------------------------------------
# MAIN (unchanged)
# ---------------------------------------------------------

def main() -> None:
    show_director = safe_dict(load_json(SHOW_DIRECTOR_PATH))
    host_intents = safe_dict(load_json(HOST_INTENTS_PATH))
    story_context_packets = safe_dict(load_json(STORY_CONTEXT_PATH))

    payload = execute_roundtable(
        show_director=show_director,
        host_intents=host_intents,
        story_context_packets=story_context_packets,
    )

    atomic_write_json(OUTPUT_JSON_PATH, TMP_OUTPUT_JSON_PATH, payload)
    write_text(OUTPUT_TXT_PATH, clean(payload.get("text_export")))

    print(f"[CONDUCTOR v3] input_director={SHOW_DIRECTOR_PATH}")
    print(f"[CONDUCTOR v3] input_host_intents={HOST_INTENTS_PATH}")
    print(f"[CONDUCTOR v3] input_story_context={STORY_CONTEXT_PATH}")
    print(f"[CONDUCTOR v3] output_json={OUTPUT_JSON_PATH}")
    print(f"[CONDUCTOR v3] output_txt={OUTPUT_TXT_PATH}")
    print(f"[CONDUCTOR v3] turns={payload.get('turn_count', 0)}")


if __name__ == "__main__":
    main()
