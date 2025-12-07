#!/usr/bin/env python3
"""
persona_router.py
ToknNews V2 — Anchor Scoring Helper for PDv4
"""

from backend.script_engine.persona.pd_rules_v4 import DOMAIN_PRIMARY, MODE_MAX_ANCHORS


def score_anchors(story, mode="NEWS"):
    """
    Score anchors based on:
     - domain primary anchor
     - meta anchor relevance (if exists)
    Returns:
        selected_anchor_list, score_dict
    """

    domain = story.get("domain", "general")
    meta   = story.get("meta", {})

    scores = {}

    # Initialize
    for anchor in DOMAIN_PRIMARY.values():
        scores[anchor] = 0.1

    # Domain primary = base anchor
    primary = DOMAIN_PRIMARY.get(domain, "chip")
    scores[primary] += 1.0

    # Meta anchor weights
    rel = meta.get("anchor_relevance", {})
    if isinstance(rel, dict):
        for a, v in rel.items():
            scores[a] = scores.get(a, 0.1) + float(v)

    # Sort by high → low
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    # Mode anchor limit
    max_n = MODE_MAX_ANCHORS.get(mode, 2)
    selected = [a for a, _ in ranked[:max_n]]

    return selected, scores
