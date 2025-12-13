#!/usr/bin/env python3
"""
grok_writer_v6.py
ToknNews — Conversational Intelligence Engine v6

Upgrades:
- GPT-4.1 support
- Phase-aware dialogue (setup → escalation → resolution)
- Tone-only memory with decay (14 days)
- Deterministic fallback
"""

from __future__ import annotations
from typing import Dict, Any, List
import time
from openai import OpenAI

from backend.runtime.vault_loader import load_secrets
from backend.script_engine.story_bank import (
    get_anchor_tone,
    update_anchor_tone,
)

# --------------------------------------------------
# OpenAI
# --------------------------------------------------
_secrets = load_secrets()
client = OpenAI(api_key=_secrets.get("openai_api_key"))


MODEL = "gpt-4.1"
TONE_DECAY_DAYS = 14


# --------------------------------------------------
# Prompt Builder
# --------------------------------------------------
def _build_prompt(story, anchors, tones, phase, latenight):
    tone_lines = []
    for a in anchors:
        t = tones.get(a, {})
        tone_lines.append(
            f"{a.capitalize()} tone: confidence={t.get('confidence',0):.2f}, "
            f"skepticism={t.get('skepticism',0):.2f}"
        )

    prompt = f"""
You are writing a ToknNews broadcast conversation.

PHASE: {phase}
MODE: {"LateNight" if latenight else "Standard"}

RULES:
- Chip leads transitions
- Anchors respond to each other
- No headlines
- 4–7 lines total
- Natural broadcast pacing

CURRENT STORY:
{story.get("summary","")}

ANCHOR TONES:
{chr(10).join(tone_lines)}

FORMAT:
Chip: ...
Cash: ...
Bond: ...
"""

    return prompt.strip()


# --------------------------------------------------
# Core Generator
# --------------------------------------------------
def generate_conversation(
    story: Dict[str,Any],
    primary: str,
    secondary: str = None,
    tertiary: str = None,
    mode: str = "NEWS",
):
    anchors = [a for a in [primary, secondary, tertiary] if a]
    latenight = mode in ("CHAOS","LATE_NIGHT")

    tones = {
        a: get_anchor_tone(a, decay_days=TONE_DECAY_DAYS)
        for a in anchors
    }

    phase = "setup"
    if story.get("importance",0) >= 7:
        phase = "escalation"
    if story.get("sentiment") == "Negative":
        phase = "aftermath"

    prompt = _build_prompt(story, anchors, tones, phase, latenight)

    try:
        rsp = client.chat.completions.create(
            model=MODEL,
            messages=[{"role":"user","content":prompt}],
            temperature=0.6 if not latenight else 0.8,
            max_tokens=600,
            timeout=20
        )
        raw = rsp.choices[0].message.content.strip()
    except Exception as e:
        print("[GWv6] GPT ERROR → fallback:", e)
        raw = f"Chip: Let's break this down.\n{primary.capitalize()}: This matters."

    lines = []
    for ln in raw.splitlines():
        if ":" not in ln:
            continue
        sp, tx = ln.split(":",1)
        speaker = sp.strip().lower()
        lines.append({
            "speaker": speaker,
            "text": tx.strip(),
            "tag": "chip_transition" if speaker=="chip" else "anchor_analysis"
        })

        # Update tone memory lightly
        update_anchor_tone(speaker, confidence_delta=0.05)

    return lines
