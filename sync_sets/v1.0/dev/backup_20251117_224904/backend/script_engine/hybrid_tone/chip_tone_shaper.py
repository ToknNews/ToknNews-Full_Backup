#!/usr/bin/env python3
"""
TOKNNews — Chip Tone Shaper (Strict Deterministic Mode)
Applies Chip's signature calm, analytical tone.
"""

REPLACEMENTS = {
    "surging": "rising",
    "exploding": "increasing",
    "crashing": "declining",
    "tanking": "pulling back",
    "moon": "gaining momentum",
    "mooning": "gaining momentum",
    "plunge": "sharp move",
    "skyrocket": "move higher"
}

def apply_chip_tone_to_line(text: str) -> str:
    """
    Applies deterministic tone smoothing.
    Removes hype, avoids slang, keeps analysis clean.
    """

    if not text:
        return text

    out = text

    for k, v in REPLACEMENTS.items():
        out = out.replace(k, v).replace(k.capitalize(), v.capitalize())

    # Remove excessive emphasis
    out = out.replace("!!", ".").replace("!", ".")

    return out.strip()
