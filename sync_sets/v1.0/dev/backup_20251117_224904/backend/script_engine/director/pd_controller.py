#!/usr/bin/env python3
"""
TOKNNews — PD Controller (Master Orchestrator)
Module C-7
"""

import time
from backend.script_engine.director.director_state import load_state, save_state
from backend.script_engine.director.segment_router import route_segment
from backend.script_engine.director.ad_logic import should_insert_ad

# === Entry point called by Script Engine V3 ===

def run_pd(headline: str):
    state = load_state()

    segment_type = route_segment(state, headline)
    anchors = select_anchors(state, headline)
    allow_bitsy = allow_bitsy_pd(state, segment_type)
    allow_vega = allow_vega_pd(state, segment_type)
    show_intro_flag = (segment_type == "show_intro")

    # update state
    state["last_segment_type"] = segment_type
    state["cycle_index"] += 1

    if show_intro_flag:
        state["intro_played"] = True

    save_state(state)

    return {
        "segment_type": segment_type,
        "anchors": anchors,
        "allow_bitsy": allow_bitsy,
        "allow_vega": allow_vega,
        "show_intro": show_intro_flag
    }


# ---------------------------------------------------------
# Anchor logic — Bible-driven, domain-aware
# ---------------------------------------------------------

def select_anchors(state, headline):
    h = headline.lower()

    # 1. Load all anchor personas from the Bible
    from script_engine.character_brain.persona_loader import get_domain

    anchor_pool = {
        "reef":  get_domain("reef"),
        "lawson": get_domain("lawson"),
        "bond": get_domain("bond"),
    }

    # 2. Score anchors by matching headline keywords to their domains
    scores = {a: 0 for a in anchor_pool}

    for anchor, domains in anchor_pool.items():
        for d in domains:
            if d.lower() in h:
                scores[anchor] += 1

    # 3. If a clear winner exists → return it
    best = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    if best[0][1] > 0:
        return [best[0][0]]

    # 4. No match → use news-cycle domain hints
    if any(k in h for k in ["sec", "regulat", "lawsuit", "compliance"]):
        return ["lawson"]

    if any(k in h for k in ["solana", "defi", "yield", "tps"]):
        return ["reef"]

    if any(k in h for k in ["macro", "market", "inflation", "rates"]):
        return ["bond"]

    # 5. Total fallback → maintain rotation
    order = ["reef", "lawson", "bond"]
    next_anchor = order[state.get("last_anchor_index", 0) % len(order)]
    state["last_anchor_index"] = (state.get("last_anchor_index", 0) + 1)
    return [next_anchor]

# ---------------------------------------------------------
# Bitsy / Vega PD control
# ---------------------------------------------------------

def allow_bitsy_pd(state, segment_type):
    if segment_type in ["breaking", "show_intro"]:
        return False
    # cooldown: once per 10 segments
    return state["cycle_index"] % 10 == 0


def allow_vega_pd(state, segment_type):
    if segment_type == "show_intro":
        return True  # Vega intro voice-over only
    if segment_type == "breaking":
        return False
    # cooldown: once per 4 segments
    return state["cycle_index"] % 4 == 0
