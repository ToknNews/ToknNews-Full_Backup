#!/usr/bin/env python3
"""
signal_boost.py
ToknNews — ToknClaw Signal Importance Booster

Boosts importance of stories related to active ToknClaw signals.
"""

def apply_signal_boost(stories):

    asset_activity = {}

    # detect ToknClaw signals
    for s in stories:

        if s.get("source") != "toknclaw":
            continue

        keys = s.get("semantic_keys", {})
        assets = keys.get("assets", [])

        for a in assets:
            asset_activity[a] = asset_activity.get(a, 0) + 1

    # apply boost
    for s in stories:

        keys = s.get("semantic_keys", {})
        assets = keys.get("assets", [])

        for a in assets:
            if a in asset_activity:

                boost = min(asset_activity[a] * 0.5, 2.5)

                s["importance"] = float(s.get("importance", 5)) + boost

    return stories
