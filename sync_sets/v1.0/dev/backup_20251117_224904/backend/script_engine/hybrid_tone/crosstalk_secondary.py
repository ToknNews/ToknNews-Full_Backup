# hybrid_tone/crosstalk_secondary.py

import random

CROSSTALK_CHIP_TO_SECONDARY = {
    "positive": [
        "{anchor}, before we move on — what’s your quick take?",
        "Feels strong — anything jump out to you, {anchor}?",
        "Momentum’s picking up — give us your angle, {anchor}."
    ],
    "neutral": [
        "{anchor}, what’s your quick pulse before we dive deeper?",
        "Give us a baseline read here, {anchor}.",
        "{anchor}, set the tone for us."
    ],
    "negative": [
        "{anchor}, this one’s rough — what’s your quick reaction?",
        "Pressure’s rising — what stands out first, {anchor}?",
        "Before we unpack this, {anchor}, what’s the problem underneath?"
    ]
}

CROSSTALK_SECONDARY_REPLY = {
    "positive": [
        "Seeing solid signals so far.",
        "Feels constructive from my side.",
        "Optimistic backdrop here."
    ],
    "neutral": [
        "Mixed picture — but let’s break it down.",
        "Some things to watch, nothing extreme yet.",
        "Neutral read for now."
    ],
    "negative": [
        "This one’s raising flags.",
        "Not a pretty setup, Chip.",
        "Short version? Pressure’s building."
    ]
}

def build_secondary_crosstalk(secondary_anchor, enriched):
    sentiment = enriched.get("sentiment", "neutral").lower()

    chip_line = random.choice(
        CROSSTALK_CHIP_TO_SECONDARY.get(sentiment, CROSSTALK_CHIP_TO_SECONDARY["neutral"])
    ).format(anchor=secondary_anchor)

    anchor_line = random.choice(
        CROSSTALK_SECONDARY_REPLY.get(sentiment, CROSSTALK_SECONDARY_REPLY["neutral"])
    )

    return chip_line, anchor_line
