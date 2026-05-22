#!/usr/bin/env python3
"""
analytics_llm.py — TEMPORARILY DISABLED

This module is deprecated for the current ToknNews production path.
It is stubbed to allow REST + Studio to boot cleanly.

Do NOT re-enable without migrating the entire codebase to the new OpenAI SDK.
"""

import os

def run_llm_analytics(*args, **kwargs):
    """
    Stubbed analytics function.
    Returns empty analytics payload.
    """
    return {
        "ok": True,
        "analytics": None,
        "note": "analytics_llm disabled"
    }
