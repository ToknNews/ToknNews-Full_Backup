#!/usr/bin/env python3
"""
pd_engine_v3.py
ToknNews 2025 — Canonical Persona Director (Transfer Brain v1.0)

PDv3 Responsibilities:
 - Select primary and secondary anchors
 - Apply breaking / hot / cold_start flags
 - Manage cast fatigue
 - Produce a stable PD context for timeline builder

This is a deterministic lightweight PD engine.
"""

import time


# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

ANCHOR_GROUPS = {
    "macro":      ["bond"],
    "regulation": ["lawson"],
    "markets":    ["cash", "bond"],
    "defi":       ["reef"],
    "onchain":    ["ledger"],
    "ai":         ["neura"],
    "culture":    ["bitsy"],
    "general":    ["chip"],
}

EXCLUDE_SECONDARY = {"chip", "vega"}  # chip = host, vega = booth-only


# -----------------------------------------------------------
# SECONDARY ANCHOR LOGIC
# -----------------------------------------------------------

def choose_secondary(primary, domain, fatigue_state):
    """
    Returns either:
        <anchor>
    or:
        None
    """

    # Domain anchors excluding primary
    candidates = [a for a in ANCHOR_GROUPS.get(domain, []) if a != primary]

    # If no domain Same-family alt, fall back to any anchor except exclusions
    if not candidates:
        all_anchors = {a for v in ANCHOR_GROUPS.values() for a in v}
        candidates = [
            a for a in all_anchors
            if a != primary and a not in EXCLUDE_SECONDARY
        ]

    # Remove fatigued anchor if over-used
    last_used = fatigue_state.get("last_secondary")
    if last_used in candidates and fatigue_state.get("secondary_streak", 0) >= 2:
        candidates = [c for c in candidates if c != last_used]

    if not candidates:
        return None

    sec = candidates[0]  # deterministic selection
    return sec


# -----------------------------------------------------------
# PD ENGINE v3 — MAIN ENTRY
# -----------------------------------------------------------

def pd_assign_roles(stories):
    """
    Takes a list of enriched+aggregated items and annotates each with:
      primary_anchor
      secondary_anchor
      flags
    """

    annotated = []
    fatigue_state = {
        "last_secondary": None,
        "secondary_streak": 0
    }

    for idx, story in enumerate(stories):
        domain = story.get("domain", "general")
        anchors = story.get("anchors", ["chip"])
        primary = anchors[0]

        breaking = bool(story.get("breaking", False))
        importance = float(story.get("importance", 5))

        # Decide secondary
        if breaking or importance >= 7:
            secondary = None
        else:
            secondary = choose_secondary(primary, domain, fatigue_state)

        # Update fatigue state
        if secondary and secondary == fatigue_state["last_secondary"]:
            fatigue_state["secondary_streak"] += 1
        else:
            fatigue_state["secondary_streak"] = 1
            fatigue_state["last_secondary"] = secondary

        flags = {
            "breaking": breaking,
            "hot": importance >= 7,
            "cold_start": idx == 0
        }

        annotated.append({
            "primary_anchor": primary,
            "secondary_anchor": secondary,
            "flags": flags
        })

    return annotated


# -----------------------------------------------------------
# FORMAT DECISION (PD CONTEXT)
# -----------------------------------------------------------

def pd_decide_format(stories):
    """
    Generates the PD context used by timeline_builder_v3.
    Transfer Brain v1.0 defaults:
      format = NEWS
      target_runtime = 180 seconds (~3 min)
    """

    role_map = pd_assign_roles(stories)

    return {
        "format": "NEWS",
        "target_runtime_sec": 180,
        "assigned_roles": role_map,
        "timestamp": time.time()
    }


# -----------------------------------------------------------
# CLI TEST
# -----------------------------------------------------------
if __name__ == "__main__":
    test = [
        {"headline": "BTC surges on ETF flows", "domain": "markets", "anchors": ["cash","bond"], "importance": 5, "breaking": False},
        {"headline": "SEC announces new hearing", "domain": "regulation", "anchors": ["lawson"], "importance": 6, "breaking": True},
    ]
    print(pd_decide_format(test))
