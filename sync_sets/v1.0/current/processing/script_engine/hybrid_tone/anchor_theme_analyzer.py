# hybrid_tone/anchor_theme_analyzer.py
"""
A-10 — Story Theme Extraction (ToknNews Theme Analyzer v1)
Chip Blue uses this to add deeper analytical framing to a story.
"""

import random

# Rule heuristics for classification
def infer_theme(enriched):
    sentiment = enriched.get("sentiment", "neutral")
    importance = int(enriched.get("importance", 5))
    domain = enriched.get("domain", "general").lower()
    headline = enriched.get("headline", "").lower()
    summary = enriched.get("summary", "").lower()

    # --- Risk Theme ---
    if "selloff" in headline or "drain" in headline or "liquidation" in headline:
        return "risk"

    if sentiment == "negative" and domain in ["markets", "defi", "security"]:
        return "risk"

    # --- Momentum Theme ---
    if "rally" in headline or "surge" in headline or "accelerates" in headline:
        return "momentum"

    if sentiment == "positive" and importance >= 7:
        return "momentum"

    # --- Structural Theme ---
    if domain in ["regulation", "legal", "policy"]:
        return "structural"

    if "infrastructure" in headline or "upgrade" in headline:
        return "structural"

    # --- Flow Theme ---
    if "funds" in headline or "inflows" in headline or "volume" in headline:
        return "flow"

    # --- Innovation Theme ---
    if domain == "ai" or "ai" in headline or "model" in headline:
        return "innovation"

    # --- Default fallback ---
    return "general"


# Theme → Chip narrative sentence
THEME_LINES = {
    "risk": [
        "This is really about risk transfer and how participants are repositioning.",
        "Risk remains the anchor theme — everything else flows from that.",
        "Under the hood, this is a risk repricing story."
    ],
    "momentum": [
        "Momentum is doing the heavy lifting here.",
        "The momentum theme is dominating the move.",
        "Upside acceleration is what's driving sentiment."
    ],
    "structural": [
        "Structurally, this is the piece that matters long-term.",
        "This is a structural shift, not just noise.",
        "Underneath, the structural theme is what will shape the next leg."
    ],
    "flow": [
        "Flows are calling the shots more than fundamentals.",
        "This one’s driven by liquidity and positioning.",
        "Flow dynamics matter more than headlines here."
    ],
    "innovation": [
        "The innovation thread is the real story here.",
        "This fits the broader innovation arc we’ve been tracking.",
        "Innovation pressure is shaping market behavior."
    ],
    "general": [
        "There’s a broader narrative forming here.",
        "Zooming out, the general theme is still developing.",
        "This story ties into the wider macro picture."
    ]
}


def generate_theme_line(enriched):
    theme = infer_theme(enriched)
    line = random.choice(THEME_LINES[theme])
    return f"Theme check: {line}"
