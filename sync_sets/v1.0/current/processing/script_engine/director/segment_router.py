#!/usr/bin/env python3
"""
TOKNNews — Segment Router
Module C-7
"""

# ------------------------------------------------------------
# Dual-Mode Imports (Package vs Local)
# ------------------------------------------------------------
try:
    from script_engine.director.breaking_logic import is_breaking
except ImportError:
    from director.breaking_logic import is_breaking

def route_segment(state, headline: str):
    # Intro only once per broadcast
    if not state["intro_played"]:
        return "show_intro"

    # Breaking news override
    if is_breaking(headline):
        return "breaking"

    # Default single headline segment
    return "headline"
