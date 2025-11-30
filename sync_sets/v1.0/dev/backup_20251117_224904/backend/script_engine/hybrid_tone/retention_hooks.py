#!/usr/bin/env python3
"""
TOKNNews Retention Hooks Engine (v1)
Adaptive hooks for Chip, Vega, and all anchors.
"""

import random


# ============================================================
# CHIP BLUE — adaptive professional hooks
# ============================================================

CHIP_HOOKS = {
    "low": [
        "Stick with us.",
        "More in a moment.",
        "Let’s keep moving.",
    ],
    "medium": [
        "You’ll want to hear the next part.",
        "This connects to something bigger.",
        "Stay with us — the picture sharpens.",
    ],
    "high": [
        "Don’t go anywhere — the next piece matters.",
        "This next development shifts the entire story.",
        "What’s coming up changes the stakes.",
    ],
}


def chip_retention_hook(enriched):
    importance = enriched.get("importance", 5)

    if importance <= 4:
        pool = CHIP_HOOKS["low"]
    elif 5 <= importance <= 7:
        pool = CHIP_HOOKS["medium"]
    else:
        pool = CHIP_HOOKS["high"]

    return random.choice(pool)


# ============================================================
# ANCHOR HOOKS — role-specific retention cues
# ============================================================

ANCHOR_HOOKS = {
    "Neura Grey": [
        "Next piece ties directly into the tech behind it.",
        "This connects to how AI systems actually behave.",
        "Stay with me — the engineering angle matters here.",
    ],
    "Reef Gold": [
        "The liquidity picture gets clearer in a second.",
        "There’s a deeper DeFi mechanic underneath this.",
        "Stick around — the pool dynamics get wild.",
    ],
    "Lawson Black": [
        "Procedure wise, the next detail is important.",
        "This part matters legally.",
        "Regulators have a pattern here — stay with me.",
    ],
    "Cap Silver": [
        "Funding momentum is shifting — more in a moment.",
        "There’s a valuation angle worth tracking next.",
        "Stay with me — the capital picture evolves quickly.",
    ],
    "Ledger Stone": [
        "The data behind this paints an even sharper picture.",
        "The on-chain numbers shift again in a moment.",
        "Stick with me — the metrics may surprise you.",
    ],
    "Bond Crimson": [
        "Zooming out, global macro ties into this next part.",
        "Markets are reacting in a predictable pattern — watch.",
        "Next piece shows the broader macro risk.",
    ],
    "Bitsy Gold": [
        "Oh you’re gonna love the next bit.",
        "Stay tuned — the timeline is losing its mind over this.",
        "Hold up — it gets even better.",
    ],
    "Penny Lane": [
        "Let me break down what this means for everyday people next.",
        "You’ll want to hear the real-world impact.",
        "Stick around — the practical side matters.",
    ],
    "Rex Vol": [
        "Oh man, the chaos ramps up next.",
        "Stick around — volatility’s just getting warmed up.",
        "You’re gonna want to see how this unfolds.",
    ],
}


def anchor_retention_hook(character):
    pool = ANCHOR_HOOKS.get(character)
    if not pool:
        return None
    return random.choice(pool)


# ============================================================
# VEGA WATT — smooth hype hooks (normal-intensity)
# ============================================================

VEGA_HOOKS = [
    "Stay tuned — energy picks up.",
    "Hold up — the next beat hits harder.",
    "Stick with us — the vibe just lifted.",
    "Keep it locked — momentum’s building.",
]


def vega_retention_hook():
    return random.choice(VEGA_HOOKS)
