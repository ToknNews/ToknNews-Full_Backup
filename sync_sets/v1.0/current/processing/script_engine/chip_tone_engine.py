# chip_tone_engine.py
"""
Chip Tone Engine
Provides tone prefixes Chip uses before tosses, transitions, recaps, etc.
"""

import random

# Unified tone table for Chip
CHIP_TONE_TABLE = {
    "positive": [
        "Promising move here —",
        "Tailwinds showing —",
        "Looking solid —",
        "Momentum’s picking up —",
    ],
    "neutral": [
        "Alright —",
        "Let’s take a steady look —",
        "Here’s where things stand —",
        "Nothing wild yet —",
    ],
    "negative": [
        "Let’s stay sharp on this one —",
        "Not ideal here —",
        "This one’s concerning —",
        "We’ve seen this pattern before —",
    ],
    "breaking": [
        "Okay — developing news right now —",
        "Stay sharp — this is moving fast —",
        "Here’s what we know at this moment —",
        "Tracking this in real time —",
    ],
    "late_night": [
        "At this hour? Alright —",
        "Still awake? Let’s walk through it —",
        "Late-night update incoming —",
        "Okay — caffeine check —",
    ],
    "high_importance": [
        "This one actually matters —",
        "Let’s hit this properly —",
        "This is one of the big stories today —",
    ],
    "low_importance": [
        "Quick one —",
        "Fast update here —",
        "Small but notable —",
    ],
}


def chip_tone_prefix(sentiment: str, importance: int, hour: int) -> str:
    """
    Selects the best tonal prefix for Chip based on story sentiment,
    importance score, and time of day.
    """

    # 1. Breaking condition is highest priority
    if importance >= 9:
        return random.choice(CHIP_TONE_TABLE["breaking"])

    # 2. High importance
    if importance >= 7:
        return random.choice(CHIP_TONE_TABLE["high_importance"])

    # 3. Late night (23–4 ET)
    if hour < 5 or hour >= 23:
        return random.choice(CHIP_TONE_TABLE["late_night"])

    # 4. Sentiment-based fallback
    if sentiment in CHIP_TONE_TABLE:
        return random.choice(CHIP_TONE_TABLE[sentiment])

    return random.choice(CHIP_TONE_TABLE["neutral"])
