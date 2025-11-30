#!/usr/bin/env python3
"""
TOKNNews — PD Controller (Master Orchestrator)
Module C-7
"""

import time
from script_engine.director.director_state import load_state, save_state
from script_engine.director.segment_router import route_segment
from script_engine.director.ad_logic import should_insert_ad

from script_engine.character_brain.persona_loader import (
    get_bible,
    get_role,
    get_domain,
    get_ensemble_behavior,
    get_relationships,
    get_segment_modes,
    get_style,
)

def classify_story(headline: str) -> dict:
    h = headline.lower()

    # ---------------------------------------------------------
    # DOMAIN ROUTING (uses Character Bible)
    # ---------------------------------------------------------
    domains = []

    # Lightweight topic inference
    if any(k in h for k in ["bitcoin", "btc", "blockchain", "halving"]):
        domains.append("macro")
        domains.append("bitcoin")

    if any(k in h for k in ["solana", "sol", "l2", "layer 2", "cosmos", "eth", "ethereum"]):
        domains.append("alts")
        domains.append("infrastructure")

    if any(k in h for k in ["hacks", "exploit", "breach", "security", "rug"]):
        domains.append("security")

    if any(k in h for k in ["meme", "memecoin", "viral", "pump", "trend"]):
        domains.append("culture")

    if any(k in h for k in ["sec", "lawsuit", "regulation", "etf", "policy"]):
        domains.append("regulation")

    # Always ensure uniqueness
    domains = list(set(domains))

    # ---------------------------------------------------------
    # SELECT CAST BASED ON DOMAINS
    # ---------------------------------------------------------
    cast = []

    for character in _BIBLE.keys():
        char_domains = get_domain(character) or []
        if any(d in char_domains for d in domains):
            cast.append(character)

    # Ensure Chip is always included as lead anchor
    if "chip" not in cast:
        cast.insert(0, "chip")

    # Fallback: if somehow empty, use default 3
    if len(cast) == 0:
        cast = ["chip", "reef", "lawson"]

    # Limit max anchors to 3 for crosstalk clarity
    cast = cast[:3]

    # The cast now contains domain-appropriate anchors

    return {
        "is_crypto": any(k in h for k in ["crypto", "bitcoin", "btc", "eth", "sol", "blockchain", "token", "nft"]),
        "is_market": any(k in h for k in ["market", "stocks", "equity", "nasdaq", "s&p", "dow"]),
        "is_regulation": any(k in h for k in ["sec", "regulation", "ban", "lawsuit", "compliance", "policy"]),
        "is_security": any(k in h for k in ["hack", "exploit", "breach", "security", "vulnerability"]),
        "is_macro": any(k in h for k in ["inflation", "fed", "interest rate", "macro"]),
        "is_viral": any(k in h for k in ["meme", "viral", "pump", "trend", "social"]),
    }

# === Entry point called by Script Engine V3 ===

def run_pd(headline: str) -> dict:
    """
    Core Programming Director routing.
    Chooses anchors, tone shift, intro rules, and chaos modules.
    """

    story = classify_story(headline)

    # -----------------------------------------------------
    # 1. PRIMARY ANCHOR SELECTION BASED ON DOMAIN MATCH
    # -----------------------------------------------------
    domain_map = {
        "reef": ["crypto", "solana", "ethereum", "markets"],
        "lawson": ["regulation", "sec", "policy", "compliance"],
        "bond": ["macro", "economy", "inflation"],
        "ivy": ["culture", "viral", "meme"],
        "penny": ["consumer", "retail"],
        "rex": ["security", "breach", "exploit"],
    }

    anchors = []

    for anchor, keywords in domain_map.items():
        if any(k in headline.lower() for k in keywords):
            anchors.append(anchor)

    # Fallback: always include 1 default anchor
    if not anchors:
        anchors = ["reef"]

    # Limit to a max of 2 anchors for crosstalk
    anchors = anchors[:2]

    # -----------------------------------------------------
    # 2. TONE SHIFT RULES
    # -----------------------------------------------------
    if story["is_security"]:
        tone_shift = "urgent"
    elif story["is_regulation"]:
        tone_shift = "serious"
    elif story["is_viral"]:
        tone_shift = "hype"
    else:
        tone_shift = None

    # -----------------------------------------------------
    # 3. CHAOS MODULES (Vega + Bitsy)
    # -----------------------------------------------------
    allow_vega = story["is_viral"] or story["is_crypto"]
    allow_bitsy = story["is_security"]

    # -----------------------------------------------------
    # 4. SHOW INTRO RULES
    # -----------------------------------------------------
    # Only show intro for major stories
    show_intro = story["is_security"] or story["is_macro"]

    # -----------------------------------------------------
    # FINAL PD CONFIG RETURN
    # -----------------------------------------------------
    return {
        "segment_type": "headline",
        "anchors": anchors,
        "allow_bitsy": allow_bitsy,
        "allow_vega": allow_vega,
        "show_intro": show_intro,
        "tone_shift": tone_shift,
    }


# ---------------------------------------------------------
# Anchor logic
# ---------------------------------------------------------

def select_anchors(state, headline):
    h = headline.lower()
    if "regulat" in h or "sec" in h:
        return ["lawson"]
    if "solana" in h or "defi" in h:
        return ["reef"]
    if "market" in h or "macro" in h or "inflation" in h:
        return ["bond"]
    # fallback: choose from last used rotation
    return ["reef", "lawson", "bond"]


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
