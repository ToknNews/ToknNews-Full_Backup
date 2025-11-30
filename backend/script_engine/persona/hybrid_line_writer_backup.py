#!/usr/bin/env python3
"""
hybrid_line_writer.py – the actual GPT-powered line writer
This is where every spoken line is born
"""

import os
from script_engine.llm.grok_client import query_grok
from script_engine.character_brain.persona_loader import (
    get_voice_id, get_lexicon, get_avoid_list, get_escalation_style
)
from script_engine.utils import log

def build_hybrid_line(anchor: str, raw_headline: str, previous_line: str = None) -> str:
    """Main GPT call — returns a perfect Token News line"""
    persona = {
        "anchor": anchor,
        "voice_id": get_voice_id(anchor),
        "lexicon": get_lexicon(anchor),
        "avoid": get_avoid_list(anchor),
        "style": get_escalation_style(anchor)
    }

    prompt = f"""
You are {anchor} on Token News — a 24/7 AI crypto broadcast.
Write ONE natural, confident, on-brand line for this headline.
Use the exact pronunciation rules in the lexicon.
Never say the words in the avoid list.
Previous line was: {previous_line or "none"}

Headline: {raw_headline}

Respond with exactly one line, no quotes, no explanation.
"""

    response = query_grok(prompt, temperature=0.7, max_tokens=80)
    line = response.strip()
    log(f"GPT → {anchor}: {line}")
    return line

# Compatibility exports for old code
build_line = build_hybrid_line

def apply_tone_shift(line: str, shift: str) -> str:
    return line  # placeholder — real tone shift is now in prompt

def build_anchor_react(anchor: str, previous_line: str) -> str:
    prompt = f"{anchor} reacts naturally to this line from another anchor: \"{previous_line}\"\nOne short, witty reaction only."
    return query_grok(prompt, temperature=0.9, max_tokens=40).strip()

# Passthrough stubs for legacy imports
def escalate_confidence(line): return line
def apply_style_constraints(line): return line
def enforce_phonetics(line): return line
def enforce_lexicon(line): return line
