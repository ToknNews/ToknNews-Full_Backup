#!/usr/bin/env python3
"""
RollingBrain v0.1 — Minimal working brain for anchor selection,
duo logic, Chip prompting, and future ingestion merging.

This version:
- stores static anchor metadata
- stores light trending topic hints
- safe structure used throughout the engine
"""

def get_brain_snapshot():
    """
    Returns a stable brain dict for the system.
    Later replaced with ingestion-fed, rolling memory.
    """

    return {
        "anchors": {
            "chip":   {"domain": ["general", "macro"],  "weight": 8},
            "reef":   {"domain": ["defi", "altcoin"],   "weight": 7},
            "lawson": {"domain": ["macro", "policy"],   "weight": 6},
            "bond":   {"domain": ["security"],          "weight": 7},
            "ledger": {"domain": ["onchain", "flows"],  "weight": 7},
            "cap":    {"domain": ["trading"],           "weight": 5},
            "neura":  {"domain": ["ai"],                "weight": 5},
            "ivy":    {"domain": ["narrative"],         "weight": 5},
            "cash":   {"domain": ["funding"],           "weight": 4},
            "rex":    {"domain": ["volatility"],        "weight": 5},
            "penny":  {"domain": ["retail"],            "weight": 6},
            "vega":   {"domain": ["vibe"],              "weight": 2},
            "bitsy":  {"domain": ["sentiment"],         "weight": 3}
        },

        # Reserved — ingestion will fill these later
        "trending_topics": [],
        "recent_events": [],
        "sentiment": {},
        "metadata": {
            "version": "0.1-minimal",
            "notes": "Replace with live ingestion later"
        }
    }

# ------------------------------------------------------------
# Context lookup for a given anchor
# Later this will use trending topics + memory ingestion.
# ------------------------------------------------------------
def get_context_for_anchor(anchor: str):
    """
    Returns a minimal context dict for the given anchor.
    This prevents import errors until full ingestion is built.
    """
    brain = get_brain_snapshot()

    # safe fallback
    if anchor not in brain["anchors"]:
        return {"topics": [], "recent": [], "sentiment": {}}

    return {
        "topics": brain.get("trending_topics", []),
        "recent": brain.get("recent_events", []),
        "sentiment": brain.get("sentiment", {}),
    }
