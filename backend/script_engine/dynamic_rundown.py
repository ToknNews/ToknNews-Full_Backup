#!/usr/bin/env python3
"""
dynamic_rundown.py
TOKEN NEWS — Dynamic Rundown Engine (2025)

Generates:
 - A natural, professional Chip rundown
 - Domain-aware grouping
 - Daypart-aware phrasing
 - PD format-aware framing
"""

import time
from typing import List, Dict

# ============================================================
# HEADLINE SHORTENER (8–12 words)
# ============================================================

def _micro(headline: str) -> str:
    words = headline.split()
    if len(words) <= 12:
        return headline
    return " ".join(words[:12]) + "…"

# ============================================================
# CHIP RUNDOWN OPENINGS
# ============================================================

OPENERS = {
    "evening": "Here’s what we’re watching tonight:",
    "morning": "Here’s what’s moving the markets this morning:",
    "afternoon": "Here’s what’s shaping the afternoon session:",
    "breaking_news": "Here’s what we know right now:",
    "deep_dive": "Before we get into the deep dive, here’s the broader backdrop:",
    "chaos_friday": "Here’s the lineup in today's chaos cycle:",
    "standard": "Here’s what we’re watching:",
}

# ============================================================
# DOMAIN LABELS (used for grouping if desired later)
# ============================================================

DOMAIN_LABELS = {
    "macro": "macro & policy",
    "regulation": "regulation",
    "markets": "market flows",
    "defi": "DeFi",
    "onchain": "on-chain activity",
    "ai": "AI & infra",
    "culture": "culture & sentiment",
    "sentiment": "sentiment",
    "general": "broader market",
}

# ============================================================
# MAIN RUNDOWN GENERATOR
# ============================================================

def generate_rundown(story_clusters: List[Dict], *, pd_context: dict, daypart: str):
    """
    Returns Chip's rundown text.
    """

    # Determine opener
    fmt = pd_context.get("format", "standard")

    if fmt == "morning_brief":
        opener = OPENERS["morning"]
    elif fmt == "breaking_news":
        opener = OPENERS["breaking_news"]
    elif fmt == "deep_dive":
        opener = OPENERS["deep_dive"]
    elif fmt == "chaos_friday":
        opener = OPENERS["chaos_friday"]
    else:
        opener = OPENERS.get(daypart, OPENERS["standard"])

    # Select top stories (PD formats may override count later)
    top_stories = story_clusters[:6]
    bullets = [f"• {_micro(item['headline'])}" for item in top_stories]

    rundown_text = opener + "\n" + "\n".join(bullets)

    return rundown_text

