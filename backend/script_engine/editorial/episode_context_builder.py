#!/usr/bin/env python3

"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS EPISODE CONTEXT BUILDER V2
Narrative Intelligence Engine

Purpose
-------
Transforms structured dialogue_blocks into a full episode brain:
• narrative-driven thesis
• segment planning
• anchor strategy (NOT assignment)
• conversation plan (debate / numeric / tone)
• thread continuity
• risk model

Author: TOKN Systems
"""

from __future__ import annotations
from typing import Any, Dict, List
from collections import Counter


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def s(x: Any) -> str:
    return "" if x is None else str(x).strip()


def f(x: Any, d: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return d


def l(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def d(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


# ---------------------------------------------------
# CORE
# ---------------------------------------------------

def build_episode_context(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:

    if not isinstance(blocks, list):
        return {}

    # -----------------------------------------
    # COLLECTION
    # -----------------------------------------

    domains = Counter()
    assets = Counter()
    threads = Counter()
    segment_types = Counter()
    signal_types = Counter()
    anchors = Counter()

    narrative_types = Counter()
    strengths = Counter()

    numeric_segments = []
    debate_segments = []
    top_lines = []

    risk_score = 0.0

    # -----------------------------------------
    # LOOP
    # -----------------------------------------

    for b in blocks:

        if not isinstance(b, dict):
            continue

        domain = s(b.get("domain") or "general")
        domains[domain] += 1

        # -------------------------------------
        # PD HINTS
        # -------------------------------------

        pd = d(b.get("pd_hints"))

        seg_type = s(pd.get("segment_type"))
        if seg_type:
            segment_types[seg_type] += 1

        thread_id = s(pd.get("thread_id"))
        if thread_id:
            threads[thread_id] += 1

        if pd.get("requires_numeric"):
            numeric_segments.append(b.get("narrative_id"))

        if pd.get("debate_potential"):
            debate_segments.append(b.get("narrative_id"))

        risk_score += f(pd.get("volatility_risk"))

        # -------------------------------------
        # CONTEXT
        # -------------------------------------

        ctx = d(b.get("context"))

        entity = s(ctx.get("entity"))
        if entity:
            assets[entity] += 1

        stype = s(ctx.get("signal_type"))
        if stype:
            signal_types[stype] += 1

        # -------------------------------------
        # SHOWRUNNER META (CRITICAL)
        # -------------------------------------

        meta = d(b.get("showrunner_meta"))

        narrative_type = s(meta.get("narrative_type"))
        if narrative_type:
            narrative_types[narrative_type] += 1

        strength = s(meta.get("strength"))
        if strength:
            strengths[strength] += 1

        # -------------------------------------
        # ANCHOR CANDIDATES
        # -------------------------------------

        for a in l(b.get("anchor_candidates")):
            a = s(a)
            if a:
                anchors[a] += 1

        # -------------------------------------
        # DIALOGUE
        # -------------------------------------

        for turn in l(b.get("dialogue")):
            text = s(d(turn).get("text"))
            if text:
                top_lines.append(text)

    # -----------------------------------------
    # DERIVED
    # -----------------------------------------

    dominant_domains = [k for k, _ in domains.most_common(3)]
    dominant_assets = [k for k, _ in assets.most_common(5)]
    dominant_narratives = [k for k, _ in narrative_types.most_common(3)]

    callback_threads = [t for t, c in threads.items() if c >= 2][:5]

    anchor_candidates = [k for k, _ in anchors.most_common(6)]

    # -----------------------------------------
    # RISK MODEL (UPGRADED)
    # -----------------------------------------

    if risk_score > 3:
        risk_direction = "fragile"
    elif risk_score < 1:
        risk_direction = "constructive"
    else:
        risk_direction = "mixed"

    # -----------------------------------------
    # EPISODE THESIS (NARRATIVE DRIVEN)
    # -----------------------------------------

    if dominant_narratives:
        episode_thesis = " | ".join(dominant_narratives[:2])
    elif dominant_domains:
        episode_thesis = f"{dominant_domains[0]} conditions are shaping the current market structure"
    else:
        episode_thesis = "Market activity is being shaped by cross-domain signals"

    # -----------------------------------------
    # SEGMENT PLAN (CRITICAL)
    # -----------------------------------------

    segment_plan = {
        "lead": [],
        "core": [],
        "filler": []
    }

    for b in blocks:
        seg = s(d(b.get("pd_hints")).get("segment_type"))
        nid = b.get("narrative_id")

        if seg == "lead":
            segment_plan["lead"].append(nid)
        elif seg == "support":
            segment_plan["core"].append(nid)
        else:
            segment_plan["filler"].append(nid)

    # -----------------------------------------
    # CONVERSATION PLAN
    # -----------------------------------------

    conversation_plan = {
        "debate_segments": debate_segments[:5],
        "numeric_segments": numeric_segments[:5],
        "tone": "analytical" if strengths.get("high", 0) > 0 else "balanced"
    }

    # -----------------------------------------
    # SIGNAL SUMMARY
    # -----------------------------------------

    signal_summary = f"{sum(signal_types.values())} structured signals across {len(domains)} domains"

    # -----------------------------------------
    # OUTPUT
    # -----------------------------------------

    return {
        "episode_thesis": episode_thesis,
        "dominant_domains": dominant_domains,
        "dominant_assets": dominant_assets,
        "dominant_narratives": dominant_narratives,
        "signal_summary": signal_summary,
        "risk_direction": risk_direction,

        # NEW STRUCTURES
        "segment_plan": segment_plan,
        "conversation_plan": conversation_plan,
        "callback_threads": callback_threads,
        "anchor_candidates": anchor_candidates,

        # SUPPORT
        "top_lines": top_lines[:5],
        "priority_signal_types": list(signal_types.keys())[:10],
    }
