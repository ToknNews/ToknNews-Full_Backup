# hybrid_tone/crosstalk.py

import random

CROSSTALK_CHIP_OPENERS = {
    "positive": [
        "Before we dive in, {anchor}, what’s your quick read?",
        "{anchor}, this one’s looking constructive — what’s your pulse?",
        "Feels like some tailwinds here — what are you seeing, {anchor}?"
    ],
    "neutral": [
        "Give us a quick pulse here, {anchor}.",
        "{anchor}, set the stage for us before we unpack this.",
        "What’s your baseline read going in?"
    ],
    "negative": [
        "{anchor}, this one’s messy — what stands out first?",
        "Before we dig in, {anchor}, what’s the problem underneath this?",
        "Give us the blunt version — what’s driving this?"
    ],
}

CROSSTALK_ANCHOR_REPLIES = {
    "positive": [
        "Looking favorable so far — momentum seems real.",
        "Tone’s solid — the numbers back it up.",
        "Optimistic signs here, Chip."
    ],
    "neutral": [
        "Mixed signals — but let’s break it down.",
        "A few things stand out, but nothing extreme yet.",
        "Steady picture so far."
    ],
    "negative": [
        "Not great — pressure’s building.",
        "This one’s raising flags.",
        "Short version? Conditions are tightening."
    ],
}


def build_crosstalk(primary_anchor, enriched):
    sentiment = enriched.get("sentiment", "neutral").lower()

    # Chip → Anchor opener
    chip_line = random.choice(
        CROSSTALK_CHIP_OPENERS.get(sentiment, CROSSTALK_CHIP_OPENERS["neutral"])
    ).format(anchor=primary_anchor)

    # Anchor → Chip response
    anchor_line = random.choice(
        CROSSTALK_ANCHOR_REPLIES.get(sentiment, CROSSTALK_ANCHOR_REPLIES["neutral"])
    )

    return chip_line, anchor_line
