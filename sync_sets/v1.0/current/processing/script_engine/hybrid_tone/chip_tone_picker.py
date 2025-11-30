#!/usr/bin/env python3
"""
chip_tone_picker.py
Provides a short, optional Chip overlay line after the main toss,
based on sentiment and importance.
"""

import random

OVERLAYS = {
    "positive": [
        "This could be bigger than it looks.",
        "Not a bad setup here.",
        "Interesting tailwind forming."
    ],
    "neutral": [
        "Let’s see where this really goes.",
        "Worth unpacking a bit.",
        "Details matter on this one."
    ],
    "negative": [
        "This one’s a bit choppy.",
        "Not ideal — let’s take a closer look.",
        "Could be more serious than it appears."
    ]
}

def pick_chip_overlay(enriched):
    sentiment = enriched.get("sentiment", "neutral").lower()
    importance = enriched.get("importance", 5)

    pool = OVERLAYS.get(sentiment, OVERLAYS["neutral"])
    line = random.choice(pool)

    # Light gating: only return overlay for medium+ importance
    if importance < 5:
        # Very low chance of overlay on low-importance stories
        if random.random() < 0.2:
            return line
        return None

    return line
