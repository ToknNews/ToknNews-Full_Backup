#!/usr/bin/env python3
"""
PD ENGINE — ToknNews Program Director v2
Controls pacing, anchor rotation, heat scoring, trio activation,
smart transitions, chaos injection, and fatigue avoidance.
"""

import random
import math

# Import persona bible
from backend.script_engine.character_brain.persona_loader import load_persona


# --------------------------
# HEAT SCORING ENGINE
# --------------------------

DOMAIN_HEAT = {
    "markets": 6,
    "macro": 7,
    "legal": 8,
    "defi": 5,
    "onchain": 5,
    "security": 9,
    "ai": 4,
    "memes": 3,
    "retail": 4,
    "venture": 4,
    "sentiment": 3,
}

KEYWORD_HEAT = {
    "sec": 3,
    "hack": 4,
    "attack": 4,
    "lawsuit": 3,
    "fomc": 3,
    "cftc": 3,
    "liquidation": 3,
    "spike": 2,
    "tumbles": 2,
    "crash": 3,
    "surge": 2,
}

def compute_heat(headline, story):
    score = 0

    # domain
    domain = story.get("domain", "sentiment").lower()
    score += DOMAIN_HEAT.get(domain, 3)

    # sentiment
    sentiment = story.get("sentiment", "Neutral").lower()
    if "negative" in sentiment:
        score += 2
    if "positive" in sentiment:
        score += 1

    # keywords
    h = headline.lower()
    for k, v in KEYWORD_HEAT.items():
        if k in h:
            score += v

    # whale or liquidation signals increase heat
    if story.get("source") in ("moralis_whales", "moralis_liquidations"):
        score += 3

    return min(score, 10)


# --------------------------
# ANCHOR SELECTION ENGINE
# --------------------------

CONFLICT_PAIRS = [
    ("cash", "bond"),
    ("reef", "ledger"),
    ("penny", "lawson"),
    ("bitsy", "chip"),   # chaos
]

def choose_primary_anchor(story):
    domain = story.get("domain", "sentiment")
    persona = load_persona(domain)
    return persona.get("name", "chip")


def choose_conflict_partner(primary):
    candidates = [b for a, b in CONFLICT_PAIRS if a == primary] + \
                 [a for a, b in CONFLICT_PAIRS if b == primary]

    if not candidates:
        return None

    return random.choice(candidates)


def maybe_add_third_anchor(heat):
    if heat >= 8:
        return random.choice(["bitsy", "reef", "cash", "neura"])
    return None


# --------------------------
# FATIGUE ENGINE
# --------------------------

def avoid_fatigue(history, anchor):
    """If anchor has spoken too much, force rotation."""
    if history.get(anchor, 0) >= 3:
        others = [a for a in history.keys() if a != anchor]
        if others:
            return random.choice(others)
    return anchor


# --------------------------
# MAIN PD DECISION FUNCTION
# --------------------------

def pd_decide(story, history):
    headline = story.get("headline", "")
    heat = compute_heat(headline, story)

    # Primary anchor (domain first)
    primary = choose_primary_anchor(story)
    primary = avoid_fatigue(history, primary)

    # Duo?
    secondary = None
    if heat >= 5:
        secondary = choose_conflict_partner(primary)

    # Trio?
    tertiary = maybe_add_third_anchor(heat)

    segment_type = (
        "trio" if tertiary else
        "duo" if secondary else
        "solo"
    )

    return {
        "heat": heat,
        "primary": primary,
        "secondary": secondary,
        "tertiary": tertiary,
        "segment_type": segment_type
    }
