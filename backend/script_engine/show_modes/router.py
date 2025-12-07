#!/usr/bin/env python3
"""
router.py
ToknNews V2 — Show Mode Router (AUTO + Manual Override)

Determines:
 - Which show mode to run
 - The story cap for that mode
 - The reason (auto vs override)
"""

import time

# Default caps per mode
MODE_CAPS = {
    "BREAKING": 1,
    "MORNING_BRIEF": 3,
    "NEWS": 5,          # your chosen default
    "HEAVY_NEWS": 8,
    "DEEP_DIVE": 1,
    "CHAOS": 10
}

# Placeholder override slot (dashboard will write to this)
OVERRIDE_PATH = "/opt/toknnews/data/mode_override.json"


def _load_override():
    try:
        import json
        with open(OVERRIDE_PATH, "r") as f:
            return json.load(f)
    except:
        return None


def detect_auto_mode(stories):
    """
    AUTO detection — lightweight for now, PDv4 will expand.
    """

    now_hour = int(time.strftime("%H"))

    # If any story is breaking → BREAKING mode
    for s in stories:
        if s.get("breaking"):
            return "BREAKING"

    # Morning hours → Morning Brief
    if 4 <= now_hour <= 10:
        return "MORNING_BRIEF"

    # Late night → CHAOS Mode
    if 22 <= now_hour or now_hour <= 2:
        return "CHAOS"

    # Default → NEWS
    return "NEWS"


def determine_show_mode(stories):
    """
    Final decision: override → auto fallback → mode caps.
    """

    override = _load_override()
    if override:
        mode = override.get("mode")
        if mode in MODE_CAPS:
            return {
                "mode": mode,
                "story_cap": MODE_CAPS[mode],
                "override": True,
                "reason": "manual_override"
            }

    # AUTO detection
    mode = detect_auto_mode(stories)
    return {
        "mode": mode,
        "story_cap": MODE_CAPS.get(mode, MODE_CAPS["NEWS"]),
        "override": False,
        "reason": "auto"
    }


if __name__ == "__main__":
    print("Router test:", determine_show_mode([]))
