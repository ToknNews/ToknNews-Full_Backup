#!/usr/bin/env python3
"""
pd_engine_v45.py
ToknNews — Persona Director Engine (PD 4.5)

Responsibilities:
 - Determine which anchor(s) cover each enriched story
 - Shape anchor combinations using composite heat + domain + memory signals
 - Apply LateNight tone modifier
 - Produce PD-ready items consumed by Timeline Builder v5

Input story fields (from EditorialEngine v4):
{
    headline: str,
    summary: str,
    domain: str,
    memory: {...},
    signals: { composite_heat: int, ... },
    persona_primary: "reef" | "cash" | "chip" | ...,
    persona_secondary: None | name,
    persona_tertiary: None | name,
    anchors: [...]
}
"""

import random
from typing import List, Dict, Any

LATE_NIGHT_DOMAINS = {"markets", "trader", "sentiment", "culture"}
LATE_NIGHT_ENERGY_BOOST = 0.35     # increases chance of playful 3-anchor exchanges
THIRD_ANCHOR_HEAT_THRESHOLD = 6    # composite_heat >= this → allow tertiary
MAX_THIRD_ANCHOR_PROB = 0.45       # 45% chance when heat is very high


# Mapping for tertiary anchor selection by domain
TERTIARY_BY_DOMAIN = {
    "defi":       "reef",
    "onchain":    "ledger",
    "regulation": "lawson",
    "markets":    "bond",
    "trader":     "cash",
    "sentiment":  "ivy",
    "culture":    "bitsy",
    "ai":         "neura",
    "general":    "chip"
}


def _pick_tertiary(domain: str, late_night: bool) -> str:
    """
    Choose a third anchor based on domain.
    If latenight → loosen rules.
    """

    if late_night:
        # playful tertiary selection
        return random.choice(list(TERTIARY_BY_DOMAIN.values()))

    return TERTIARY_BY_DOMAIN.get(domain, "chip")


def pd_engine(stories: List[Dict[str, Any]], mode: str = "NEWS", latenight: bool = False):
    """
    MASTER PD FUNCTION
    Produces list of PD dicts:

    {
        "story": <enriched story>,
        "primary": "cash",
        "secondary": "bond",
        "tertiary": None or name,
        "anchors": [primary, secondary, tertiary?]
    }
    """

    pd_out = []

    for story in stories:

        domain   = story.get("domain", "general")
        primary  = story.get("persona_primary", "chip")
        secondary= story.get("persona_secondary")
        heat     = story.get("signals", {}).get("composite_heat", 0)

        # -----------------------------
        # SECONDARY ANCHOR RULES
        # -----------------------------
        if not secondary:
            # Basic fallback pairing
            if primary == "chip":
                secondary = None
            elif primary in ("cash", "bond") and domain == "markets":
                secondary = "chip"
            elif primary == "reef" and domain in ("defi","onchain"):
                secondary = "ledger"
            else:
                secondary = None

        # -----------------------------
        # TERTIARY ANCHOR RULES
        # heat-driven + latenight looseness
        # -----------------------------
        tertiary = None
        allow_third = False

        if heat >= THIRD_ANCHOR_HEAT_THRESHOLD:
            allow_third = True
        if latenight and domain in LATE_NIGHT_DOMAINS:
            allow_third = True

        if allow_third:
            base_prob = min(MAX_THIRD_ANCHOR_PROB, heat / 12)

            if latenight:
                base_prob += LATE_NIGHT_ENERGY_BOOST

            if random.random() < base_prob:
                tertiary = _pick_tertiary(domain, latenight)

        # -----------------------------
        # Build anchor list
        # -----------------------------
        anchors = [primary]
        if secondary:
            anchors.append(secondary)
        if tertiary:
            anchors.append(tertiary)

        pd_out.append({
            "story": story,
            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "anchors": anchors,
            "heat": heat,
            "domain": domain
        })

    return pd_out


if __name__ == "__main__":
    print("PD Engine v4.5 loaded.")
