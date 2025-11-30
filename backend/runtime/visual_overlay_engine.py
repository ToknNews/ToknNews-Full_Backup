#!/usr/bin/env python3
"""
visual_overlay_engine.py
TOKEN NEWS — Visual Overlay Metadata Generator

This engine attaches metadata to timeline blocks for use in:
 - Unreal Engine
 - CapCut templates
 - FFmpeg post passes
 - After Effects graphics
 - TikTok/Shortform overlay renderers

It does NOT perform rendering — it only generates metadata payloads.
"""

import time
import uuid


# ============================================================
# CATEGORY COLOR MAPPING
# ============================================================

CATEGORY_COLORS = {
    "breaking":   {"bg": "#FF0033", "fg": "#FFFFFF"},
    "macro":      {"bg": "#005BBB", "fg": "#FFFFFF"},
    "markets":    {"bg": "#0033AA", "fg": "#FFFFFF"},
    "defi":       {"bg": "#009977", "fg": "#FFFFFF"},
    "onchain":    {"bg": "#2277FF", "fg": "#FFFFFF"},
    "regulation": {"bg": "#AA2200", "fg": "#FFFFFF"},
    "ai":         {"bg": "#8844FF", "fg": "#FFFFFF"},
    "retail":     {"bg": "#FF8800", "fg": "#000000"},
    "sentiment":  {"bg": "#CC33CC", "fg": "#FFFFFF"},
    "meta":       {"bg": "#666666", "fg": "#FFFFFF"},
    "general":    {"bg": "#222222", "fg": "#FFFFFF"},
}


# ============================================================
# LOWER THIRD GENERATOR
# ============================================================

def build_lower_third(speaker: str) -> str:
    speaker = speaker.lower()

    if speaker == "chip":
        return "Chip Blue — Rational Anchor"
    if speaker == "reef":
        return "Reef Gold — DeFi Specialist"
    if speaker == "lawson":
        return "Lawson Black — Regulation & Policy"
    if speaker == "bond":
        return "Bond Crimson — Macro Strategist"
    if speaker == "ivy":
        return "Ivy Quinn — Behavioral Economics"
    if speaker == "cash":
        return "Cash Green — Retail Psychology"
    if speaker == "ledger":
        return "Ledger Stone — On-Chain Analyst"
    if speaker == "penny":
        return "Penny Lane — Retail & Human Interest"
    if speaker == "bitsy":
        return "Bitsy Gold — Meta Interruption"
    if speaker == "rex":
        return "Rex Vol — Night Volatility"
    if speaker == "neura":
        return "Neura Grey — AI & Compute"
    if speaker == "cap":
        return "Cap Silver — Venture & Funding"
    if speaker == "vega":
        return "Vega Watt — Booth Voice"

    return f"{speaker.capitalize()} — Anchor"


# ============================================================
# TICKER TEXT BUILDER
# ============================================================

def build_ticker_text(headline: str, category: str) -> str:
    if category == "breaking":
        return f"BREAKING: {headline}"
    return headline[:140]  # safe cutoff


# ============================================================
# SPLASH / HEADLINE STING
# ============================================================

def build_splash(headline: str, category: str) -> dict:
    return {
        "splash_id": uuid.uuid4().hex[:8],
        "headline": headline,
        "category": category,
        "timestamp": time.time()
    }

# ============================================================
# CATEGORY DETECTION
# ============================================================

def infer_category(domain: str, is_breaking: bool) -> str:
    if is_breaking:
        return "breaking"

    domain = (domain or "general").lower()

    if domain in CATEGORY_COLORS:
        return domain

    return "general"


# ============================================================
# OVERLAY PAYLOAD BUILDER
# ============================================================

def build_overlay_payload(block, story, pd_flags):
    """
    Given a timeline block and its story context, build a graphical overlay metadata dict.
    """

    headline = story.get("headline", "")
    domain   = story.get("domain", "general")
    is_breaking = pd_flags.get("is_breaking", False)

    category = infer_category(domain, is_breaking)
    colors   = CATEGORY_COLORS.get(category, CATEGORY_COLORS["general"])

    return {
        "headline": headline,
        "category": category,
        "color_theme": colors,
        "ticker": build_ticker_text(headline, category),
        "lower_third": build_lower_third(block["speaker"]),
        "splash": build_splash(headline, category),
        "style": {
            "animate_in": True,
            "animate_out": True,
            "duration_hint": "auto"
        }
    }


# ============================================================
# APPLY OVERLAYS TO TIMELINE BLOCKS
# ============================================================

def apply_overlays_to_timeline(blocks, selected_stories, pd_configs):
    """
    Attach metadata to each timeline block:
      block["visual_overlay"] = {...}

    selected_stories: list of story dicts
    pd_configs: parallel array of PD outputs for each story
    """

    story_idx = 0
    story_len = len(selected_stories)

    for i, block in enumerate(blocks):

        # Map block to story index safely
        if story_idx >= story_len:
            story_idx = story_len - 1

        story = selected_stories[story_idx]
        pd_flags = pd_configs[story_idx].get("pd_flags", {})

        # Build overlay payload
        overlay = build_overlay_payload(block, story, pd_flags)

        # Attach to block
        block["visual_overlay"] = overlay

        # Move to next story after certain block types
        if block["block_type"] in ["chip_transition", "duo_exchange", "anchor_analysis"]:
            story_idx += 1

    return blocks
