#!/usr/bin/env python3
"""
TOKNNews — Segment Router
Module C-7
"""

from script_engine.director.breaking_logic import is_breaking
from script_engine.director.cast_fatigue import should_rotate_cast
from script_engine.director.hijinx_rules import should_trigger_hijinx


def route_segment(headline: str, state: dict):
    """
    Determines which segment type should run next.
    """

    # Intro only once
    if not state.get("intro_played", False):
        return "show_intro"

    # Breaking news override
    if is_breaking(headline):
        return "breaking"

    # TODO (Phase 2): Add domain → anchor routing
    # TODO (Phase 3): Add hijinx gating and stress-level routing

    # Default: single headline coverage
    return "headline"
