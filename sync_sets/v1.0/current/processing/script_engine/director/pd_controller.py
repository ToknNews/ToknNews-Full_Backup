#!/usr/bin/env python3
"""
TOKNNews — PD Controller (Master Orchestrator)
Module C-7
"""

import time

# ------------------------------------------------------------
# Dual-Mode Imports (Package vs Local)
# ------------------------------------------------------------
try:
    from script_engine.director.director_state import load_state, save_state
    from script_engine.director.segment_router import route_segment
    from script_engine.director.ad_logic import should_insert_ad
except ImportError:
    from director.director_state import load_state, save_state
    from director.segment_router import route_segment
    from director.ad_logic import should_insert_ad

# ============================================================================
# STEP 3-G — Character-Bible Driven Anchor Logic
# ============================================================================

def select_anchors(state, headline, personas):
    """
    Step-3G Anchor Logic:
    - Domain scoring
    - Bible roles
    - Duo support
    """
    pd_directive = state.get("pd_directive")
    tone_shift = state.get("tone_shift")
    primary_domain = state.get("primary_domain")

    # Build candidate pool
    candidates = []
    for name, p in personas.items():

        # Normalize Bible fields
        roles = p.get("role") or p.get("roles") or []
        if isinstance(roles, str):
            roles = [roles]

        domains = p.get("domain") or p.get("domains") or []
        if isinstance(domains, str):
            domains = [domains]

        duo_with = p.get("duo_with") or p.get("duo") or []

        tone_bias = p.get("tone_bias") or []
        if isinstance(tone_bias, str):
            tone_bias = [tone_bias]

        voice_id = p.get("voice_id") or p.get("voice")

        candidates.append({
            "name": name,
            "roles": roles,
            "domains": domains,
            "duo_with": duo_with,
            "tone_bias": tone_bias,
            "voice_id": voice_id
        })

    # PD override
    if pd_directive and pd_directive in personas:
        return [pd_directive]

    scores = {}
    hl = headline.lower()

    # Scoring
    for c in candidates:
        score = 0

        # Domain match
        if primary_domain and primary_domain in c["domains"]:
            score += 20

        # Headline keywords
        for d in c["domains"]:
            if d.lower() in hl:
                score += 5

        # Role priority
        if "primary_anchor" in c["roles"]:
            score += 10
        if "analyst" in c["roles"]:
            score += 4
        if "contrarian" in c["roles"]:
            score += 2

        # Tone bias
        if tone_shift and tone_shift in c["tone_bias"]:
            score += 3

        scores[c["name"]] = score

    # Top anchor
    top = max(scores, key=scores.get)
    primary = [top]

    # --- Domain-based duo selection ---
    DUO_BY_DOMAIN = {
        "defi":        ["ledger", "cash"],
        "onchain":     ["reef", "bond"],
        "markets":     ["cash", "bond"],
        "macro":       ["bond", "lawson"],
        "regulation":  ["lawson", "bond"],
        "ai":          ["neura", "cap"],
        "funding":     ["cap", "neura"],
        "meme":        ["bitsy", "penny"],
        "retail":      ["penny", "bitsy"],
        "volatility":  ["rex", "reef", "cash"],
        "general":     ["chip", "bond", "ivy"]
    }

    duo_candidates = DUO_BY_DOMAIN.get(primary_domain, [])
    duo_partner = None

    # Choose the first valid persona in the duo list that exists
    for cand in duo_candidates:
        if cand in personas and cand != top:
            duo_partner = cand
            break

    if duo_partner:
        primary.append(duo_partner)

    return primary


# ============================================================================
# PD ENTRY POINT (final Step-3G version — ONLY ONE)
# ============================================================================

def run_pd(headline: str, personas: dict):
    state = load_state()
    print("DEBUG PERSONAS:", personas.keys())

    # ---------------------------
    # Step-3G Domain Detection
    # ---------------------------
    hl = headline.lower()

    if any(x in hl for x in ["defi", "exploit", "liquidity", "amm"]):
        state["primary_domain"] = "defi"
    elif any(x in hl for x in ["sec", "cftc", "lawsuit", "regulator"]):
        state["primary_domain"] = "regulation"
    elif any(x in hl for x in ["ai", "language model", "gpu"]):
        state["primary_domain"] = "ai"
    elif any(x in hl for x in ["on-chain", "onchain", "wallet", "addresses"]):
        state["primary_domain"] = "onchain"
    elif any(x in hl for x in ["cpi", "macro", "inflation"]):
        state["primary_domain"] = "macro"
    elif any(x in hl for x in ["funding", "venture", "seed round"]):
        state["primary_domain"] = "funding"
    elif any(x in hl for x in ["meme", "culture", "community"]):
        state["primary_domain"] = "meme"
    elif any(x in hl for x in ["retail", "users", "customer"]):
        state["primary_domain"] = "retail"
    elif any(x in hl for x in ["volatility", "liquidations", "night", "chaos"]):
        state["primary_domain"] = "volatility"
    else:
        state["primary_domain"] = "general"

    # ---------------------------
    # Segment routing
    # ---------------------------
    segment_type = route_segment(state, headline)

    # ---------------------------
    # Anchor selection
    # ---------------------------
    anchors = select_anchors(state, headline, personas)

    # ---------------------------
    # Bitsy / Vega triggers
    # ---------------------------
    allow_bitsy = allow_bitsy_pd(state, segment_type)
    allow_vega = allow_vega_pd(state, segment_type)
    show_intro = (segment_type == "show_intro")

    # ---------------------------
    # State update
    # ---------------------------
    state["last_segment_type"] = segment_type
    state["cycle_index"] += 1
    if show_intro:
        state["intro_played"] = True

    save_state(state)

    # ---------------------------
    # Return PD config
    # ---------------------------
    return {
        "segment_type": segment_type,
        "primary_domain": state["primary_domain"],
        "anchors": anchors,
        "allow_bitsy": allow_bitsy,
        "allow_vega": allow_vega,
        "show_intro": show_intro
    }


# ============================================================================
# Bitsy / Vega PD Control
# ============================================================================

def allow_bitsy_pd(state, segment_type):
    if segment_type in ["breaking", "show_intro"]:
        return False
    return state["cycle_index"] % 10 == 0


def allow_vega_pd(state, segment_type):
    if segment_type == "show_intro":
        return True
    if segment_type == "breaking":
        return False
    return state["cycle_index"] % 4 == 0
