#!/usr/bin/env python3
"""
ad_engine.py
TOKEN NEWS — AD INSERTION ENGINE (2025)

Handles:
 - Global ad on/off toggle
 - Modes: disabled / fixed / smart
 - Vega-only VO for ad reads
 - Sponsor-defined copy (future dashboard-driven)
 - PD-aware insertion rules
 - Runtime-aware throttling
"""

import time
from typing import Optional, Dict

# ============================================================
# DEFAULT CONFIG (Dashboard will override later)
# ============================================================

AD_CONFIG = {
    "enabled": False,                 # Master toggle OFF by default
    "mode": "disabled",               # Options: disabled, fixed, smart
    "voice_style": "professional",    # V2 (your chosen default)
    "sponsor_name": None,
    "ad_copy": None,                  # Full sponsor message (future dashboard)
    "min_gap_seconds": 120,           # Minimum runtime gap between ads
    "last_ad_timestamp": 0,
}

# ============================================================
# AD COPY TEMPLATE (V2 Professional Default)
# ============================================================

DEFAULT_AD_COPY = (
    "Today's episode of ToknNews is brought to you by our partners. "
    "Supporting the tools and infrastructure that keep the crypto markets moving."
)

# ============================================================
# INTERNAL: BUILD AD BLOCK
# ============================================================

def _build_ad_block(voice_style: str, sponsor_copy: Optional[str]) -> Dict:
    """
    Returns a ready-to-insert timeline block for Vega to read.
    """
    text = sponsor_copy or DEFAULT_AD_COPY

    # All ads are spoken by Vega, booth voice only.
    return {
        "speaker": "vega",
        "text": text,
        "tag": "ad_read",
        "timestamp": time.time(),
    }

# ============================================================
# DETERMINE IF AD SHOULD BE INSERTED
# ============================================================

def _should_insert_ad(estimated_runtime_sec: float) -> bool:
    """
    Determines if we can insert an ad based on time gap.
    """
    now = time.time()

    # Not enough gap since last ad
    if now - AD_CONFIG["last_ad_timestamp"] < AD_CONFIG["min_gap_seconds"]:
        return False

    # Runtime constraints (only if runtime > 3 minutes)
    if estimated_runtime_sec < 180:
        return False

    return True

# ============================================================
# PUBLIC API: maybe_insert_ad()
# ============================================================

def maybe_insert_ad(
    *,
    pd_context: dict,
    estimated_runtime_sec: float,
    segment_index: int
) -> Optional[Dict]:
    """
    Called by timeline_builder_v3 during block construction.

    Returns:
        None → no ad inserted
        Dict → ad block to append to timeline
    """

    # MASTER TOGGLE
    if not AD_CONFIG["enabled"]:
        return None

    mode = AD_CONFIG["mode"]

    # -------------------------------------
    # MODE: DISABLED
    # -------------------------------------
    if mode == "disabled":
        return None

    # -------------------------------------
    # MODE: FIXED (simple, predictable)
    # -------------------------------------
    if mode == "fixed":
        # Insert AFTER rundown (segment_index == 1)
        if segment_index == 1 and _should_insert_ad(estimated_runtime_sec):
            AD_CONFIG["last_ad_timestamp"] = time.time()
            return _build_ad_block(
                AD_CONFIG["voice_style"],
                AD_CONFIG["ad_copy"]
            )
        return None

    # -------------------------------------
    # MODE: SMART (PD-driven)
    # -------------------------------------
    if mode == "smart":

        # PD rule: breaking news = minimal ads
        if pd_context.get("format") == "breaking_news":
            return None

        # PD rule: deep dive → ad BEFORE deep dive
        if pd_context.get("format") == "deep_dive" and segment_index == 0:
            if _should_insert_ad(estimated_runtime_sec):
                AD_CONFIG["last_ad_timestamp"] = time.time()
                return _build_ad_block(
                    AD_CONFIG["voice_style"],
                    AD_CONFIG["ad_copy"]
                )
            return None

        # PD rule: chaos friday → ads mid-show only
        if pd_context.get("format") == "chaos_friday" and segment_index == 2:
            if _should_insert_ad(estimated_runtime_sec):
                AD_CONFIG["last_ad_timestamp"] = time.time()
                return _build_ad_block(
                    AD_CONFIG["voice_style"],
                    AD_CONFIG["ad_copy"]
                )
            return None

        # PD rule: standard → spaced by time + runtime
        if pd_context.get("format") == "standard":
            if _should_insert_ad(estimated_runtime_sec) and segment_index % 3 == 0:
                AD_CONFIG["last_ad_timestamp"] = time.time()
                return _build_ad_block(
                    AD_CONFIG["voice_style"],
                    AD_CONFIG["ad_copy"]
                )
        return None

    # -------------------------------------
    # Unknown mode
    # -------------------------------------
    return None

