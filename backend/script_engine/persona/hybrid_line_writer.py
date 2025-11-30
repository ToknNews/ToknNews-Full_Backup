#!/usr/bin/env python3
"""
hybrid_line_writer.py – bulletproof dry-run version (Nov 22 2025)
No external imports, no llm folder, no grok_client needed
"""

import os
import random

# Fake Grok responses when TTS is disabled (which it always is right now)
def query_grok(prompt, temperature=0.7, max_tokens=100):
    fake_lines = [
        "Bitcoin just crossed ninety-three thousand dollars.",
        "ETF inflows are hitting record after record.",
        "This is the fastest bull market we've ever witnessed.",
        "On-chain volume just exploded again.",
        "The liquidity tsunami is here.",
        "Someone just stacked another billion in BTC.",
        "We are so back.",
        "Holy conviction, Batman.",
    ]
    line = random.choice(fake_lines)
    print(f"[DRY-RUN] Grok → {line}")
    return line

# Main function everything calls
def build_hybrid_line(anchor: str, raw_headline: str, previous_line: str = None) -> str:
    prompt = f"Write one perfect Token News line for {anchor} about: {raw_headline}"
    return query_grok(prompt)

# Compatibility exports so nothing else has to change
build_line = build_hybrid_line
apply_tone_shift = lambda line, shift: line
build_anchor_react = lambda anchor, line: f"Wow, {anchor} wasn't kidding..."
escalate_confidence = lambda line: line
apply_style_constraints = lambda line: line
enforce_phonetics = lambda line: line
enforce_lexicon = lambda line: line

__all__ = [
    "build_hybrid_line", "build_line", "apply_tone_shift", "build_anchor_react",
    "escalate_confidence", "apply_style_constraints", "enforce_phonetics", "enforce_lexicon"
]
