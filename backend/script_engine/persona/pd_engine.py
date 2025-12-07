#!/usr/bin/env python3
"""
pd_engine.py
ToknNews V2 — Persona Director v4 (Consolidated Version)

Replaces PDv3 entirely.

Outputs for each story:
{
    "story": <story dict>,
    "anchors": [...],
    "primary": "...",
    "secondary": "...",
    "tertiary": "...",
    "tone": {...},
    "flags": {...},
    "pd_notes": "..."
}
"""

import time
from backend.script_engine.persona.pd_state import (
    load_pd_state, save_pd_state, update_anchor_usage
)

# --------------------------
# BASELINE ANCHOR MAPS
# --------------------------

ANCHORS = [
    "chip", "bond", "cash", "ledger", "neura",
    "reef", "lawson", "bitsy", "penny", "rex"
]

DOMAIN_PRIMARY = {
    "macro": "bond",
    "markets": "cash",
    "defi": "reef",
    "onchain": "ledger",
    "ai": "neura",
    "regulation": "lawson",
    "culture": "bitsy",
    "general": "chip",
}

MODE_MAX_ANCHORS = {
    "BREAKING": 1,
    "MORNING_BRIEF": 1,
    "NEWS": 2,
    "HEAVY_NEWS": 3,
    "DEEP_DIVE": 1,
    "CHAOS": 3
}

TONE_RULES = {
    "risk_on":    {"energy":"upbeat",   "pace":"medium"},
    "risk_off":   {"energy":"serious",  "pace":"slow"},
    "volatile":   {"energy":"alert",    "pace":"fast"},
    "culture":    {"energy":"loose",    "pace":"medium"},
    "flat":       {"energy":"neutral",  "pace":"medium"},
}


def _tone_from_cluster(cluster):
    return TONE_RULES.get(cluster, TONE_RULES["flat"])


# --------------------------
# PDv4 CORE LOGIC
# --------------------------

def _score_anchors(story, mode, state):
    """
    Generate anchor score table using:
     - domain primary anchor
     - meta anchor relevance (if exists)
     - fatigue (handled later)
    """
    domain = story.get("domain", "general")
    meta   = story.get("meta", {})

    scores = {a: 0.1 for a in ANCHORS}

    # Domain boost
    domain_anchor = DOMAIN_PRIMARY.get(domain, "chip")
    scores[domain_anchor] += 1.0

    # Meta anchor relevance boosts
    rel = meta.get("anchor_relevance")
    if isinstance(rel, dict):
        for a, v in rel.items():
            if a in scores:
                scores[a] += float(v)

    return scores


def _apply_fatigue(scores, state):
    usage = state.get("anchor_usage", {})

    for a in scores:
        if usage.get(a, 0) > 4:
            scores[a] *= 0.7
        if usage.get(a, 0) > 7:
            scores[a] *= 0.5

    return scores


def _mode_aware_fallback(story, mode):
    """
    Fallback casting when no meta exists. 
    Real-world newsroom behavior.
    """

    domain = story.get("domain", "general")
    primary = DOMAIN_PRIMARY.get(domain, "chip")

    if mode == "BREAKING":
        return [primary]

    if mode == "MORNING_BRIEF":
        return ["chip"]

    if mode == "NEWS":
        return ["chip", primary]

    if mode == "HEAVY_NEWS":
        # add least overused anchor
        return ["chip", primary]

    if mode == "DEEP_DIVE":
        return [primary]

    if mode == "CHAOS":
        return ["chip", primary, "bitsy"]

    return ["chip", primary]


def pd_engine(stories, mode="NEWS"):
    """
    MASTER PDv4 controller.
    Replaces PDv3 entirely.
    """

    state = load_pd_state()
    results = []

    for story in stories:

        meta = story.get("meta")

        # ---------------------------------------
        # ANCHOR SELECTION
        # ---------------------------------------
        if meta:  
            # Score anchors
            scores = _score_anchors(story, mode, state)
            scores = _apply_fatigue(scores, state)

            # Select top anchors allowed by mode
            ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            max_n = MODE_MAX_ANCHORS.get(mode, 2)
            anchors = [a for a, _ in ranked[:max_n]]

            pd_notes = "Meta-driven casting based on anchor relevance + fatigue."
        else:
            # MODE-AWARE FALLBACK
            anchors = _mode_aware_fallback(story, mode)
            pd_notes = "Fallback casting: no meta available; mode-aware domain mapping applied."

        # ---------------------------------------
        # PRIMARY / SECONDARY / TERTIARY
        # ---------------------------------------
        primary   = anchors[0] if len(anchors) > 0 else "chip"
        secondary = anchors[1] if len(anchors) > 1 else None
        tertiary  = anchors[2] if len(anchors) > 2 else None

        # ---------------------------------------
        # TONE SHAPING
        # ---------------------------------------
        cluster = None
        if meta:
            cluster = meta.get("narrative_cluster", "flat")
        tone = _tone_from_cluster(cluster)

        # ---------------------------------------
        # FLAGS
        # ---------------------------------------
        flags = {
            "breaking": story.get("breaking", False),
            "chaos_mode": (mode == "CHAOS"),
            "deep_mode": (mode == "DEEP_DIVE")
        }

        # ---------------------------------------
        # UPDATE STATE
        # ---------------------------------------
        state = update_anchor_usage(state, anchors)

        # ---------------------------------------
        # APPEND FINAL OUTPUT
        # ---------------------------------------
        results.append({
            "story": story,
            "anchors": anchors,
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "tone": tone,
            "flags": flags,
            "pd_notes": pd_notes
        })

    save_pd_state(state)
    return results


if __name__ == "__main__":
    print("PDv4 Loaded.")
