#!/usr/bin/env python3
"""
ad_engine.py
ToknNews 2025 — Canonical Lightweight Ad Engine (Transfer Brain v1.0)

Rules:
 - No ads for Breaking or Morning Brief formats.
 - Only insert ads if PD format is NEWS and runtime > 120 seconds.
 - Only insert ads at segment_index == 1 (post-rundown) or mid-show slots.
 - Return None if no ad should be inserted.
"""

def maybe_insert_ad(pd_context=None, estimated_runtime_sec=0, segment_index=0):
    """
    Inputs:
      pd_context: dict from PDv3
      estimated_runtime_sec: float
      segment_index: int (1 = after rundown)

    Returns:
      None  (no ad)
      or
      { "text": "..." }
    """

    if pd_context is None:
        return None

    fmt = pd_context.get("format", "NEWS")

    # Only NEWS format uses ads in v1.0
    if fmt != "NEWS":
        return None

    # Only insert ads if runtime exceeds 120 seconds (2 mins)
    if estimated_runtime_sec < 120:
        return None

    # Ad slots:
    #  segment_index == 1  → after rundown
    #  segment_index > 1   → mid-show intervals
    if segment_index == 1:
        return {
            "text": "This segment is brought to you by ToknNews Premium — stay informed."
        }

    # Optional mid-show ad every ~3 stories
    if segment_index % 3 == 0:
        return {
            "text": "Enjoying the coverage? Upgrade to ToknNews Premium for full deep dives."
        }

    return None


if __name__ == "__main__":
    print("[AD] ad_engine (Transfer Brain v1.0) loaded.")
