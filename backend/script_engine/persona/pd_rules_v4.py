#!/usr/bin/env python3
"""
pd_rules_v4.py
ToknNews V2 — Rules and Weights for PDv4
"""

# Anchor list
ANCHORS = [
    "chip", "bond", "cash", "ledger", "neura",
    "reef", "lawson", "bitsy", "penny", "rex"
]

# Domain → primary anchor mapping
DOMAIN_PRIMARY = {
    "macro": "bond",
    "markets": "cash",
    "defi": "reef",
    "onchain": "ledger",
    "ai": "neura",
    "regulation": "lawson",
    "culture": "bitsy",
    "general": "chip"
}

# Maximum anchors allowed per mode
MODE_MAX_ANCHORS = {
    "BREAKING": 1,
    "MORNING_BRIEF": 1,
    "NEWS": 2,
    "HEAVY_NEWS": 3,
    "DEEP_DIVE": 1,
    "CHAOS": 3
}

# Tone presets based on narrative cluster
TONE_RULES = {
    "risk_on":    {"energy": "upbeat",   "pace": "medium"},
    "risk_off":   {"energy": "serious",  "pace": "slow"},
    "volatile":   {"energy": "alert",    "pace": "fast"},
    "culture":    {"energy": "loose",    "pace": "medium"},
    "flat":       {"energy": "neutral",  "pace": "medium"}
}

def get_tone_from_cluster(cluster):
    """Return tone settings based on narrative cluster."""
    return TONE_RULES.get(cluster, TONE_RULES["flat"])
