#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS PD ENGINE v5 (PRODUCTION)
Orchestration + Anchor Intelligence Layer

Purpose
-------
Final authority for:
- anchor selection (from candidates)
- fatigue rotation
- mode constraints
- segment weighting

DOES NOT:
- re-route domains
- overwrite ingest intelligence

Author: TOKN Systems
"""

from __future__ import annotations

import random
from typing import List, Dict, Any

from backend.script_engine.persona.pd_state import load_pd_state, save_pd_state, update_anchor_usage
from backend.script_engine.persona.pd_rules_v4 import MODE_MAX_ANCHORS


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def _safe_list(x):
    return x if isinstance(x, list) else []

def _safe_dict(x):
    return x if isinstance(x, dict) else {}

def _safe_str(x):
    return "" if x is None else str(x).lower().strip()


# ---------------------------------------------------
# FATIGUE SCORING
# ---------------------------------------------------

def _score_anchor(anchor: str, state: dict) -> float:
    usage = state["anchor_usage"].get(anchor, 0)
    return 1.0 / (1 + usage)  # lower usage = higher score


# ---------------------------------------------------
# CORE SELECTION
# ---------------------------------------------------

def _select_anchors(block: dict, state: dict, mode: str) -> List[str]:

    candidates = [
        _safe_str(a)
        for a in _safe_list(block.get("anchor_candidates"))
        if _safe_str(a)
    ]

    if not candidates:
        candidates = ["chip"]

    # score by fatigue
    scored = sorted(
        candidates,
        key=lambda a: _score_anchor(a, state),
        reverse=True
    )

    max_allowed = MODE_MAX_ANCHORS.get(mode, 2)

    return scored[:max_allowed]


# ---------------------------------------------------
# MAIN ENGINE
# ---------------------------------------------------

def pd_engine(
    segments: List[Dict[str, Any]],
    *,
    mode: str = "NEWS",
    latenight: bool = False
) -> List[Dict[str, Any]]:

    state = load_pd_state()
    output = []

    for seg in segments:

        pd_hints = _safe_dict(seg.get("pd_hints"))
        segment_type = pd_hints.get("segment_type", "support")
        heat = seg.get("heat", 5)

        anchors = _select_anchors(seg, state, mode)

        primary = anchors[0] if anchors else "chip"
        secondary = anchors[1] if len(anchors) > 1 else None
        tertiary = anchors[2] if len(anchors) > 2 else None

        # runtime scaling
        base_runtime = 45
        runtime = int(base_runtime * (1 + max(0, heat - 5) / 10))
        runtime = max(25, min(90, runtime))

        # energy scaling
        energy = 0.6 + (heat / 20)
        if latenight:
            energy += 0.2

        output.append({
            "story": seg,
            "domain": seg.get("domain"),
            "heat": heat,

            "primary": primary,
            "secondary": secondary,
            "tertiary": tertiary,
            "anchors": anchors,
            "speaking_order": anchors,

            "pd_hints": pd_hints,
            "segment_type": segment_type,

            "runtime_suggested_sec": runtime,
            "energy_level": round(min(1.0, energy), 2),
        })

        state = update_anchor_usage(state, anchors)

    save_pd_state(state)
    return output


if __name__ == "__main__":
    print("PD Engine v5 loaded")
