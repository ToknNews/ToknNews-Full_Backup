#!/usr/bin/env python3
"""
signal_fusion.py
ToknNews — Signal/News Fusion Layer
"""

def apply_signal_boost(stories):

    asset_signals = {}

    # detect signals
    for s in stories:

        if s.get("source") != "toknclaw":
            continue

        assets = s.get("semantic_keys", {}).get("assets", [])

        for a in assets:
            asset_signals[a] = asset_signals.get(a, 0) + 1

    # boost related stories
    for s in stories:

        if s.get("source") == "toknclaw":
            continue

        assets = s.get("semantic_keys", {}).get("assets", [])

        for a in assets:

            if a in asset_signals:

                boost = min(asset_signals[a] * 0.7, 3)

                s["importance"] = float(s.get("importance", 5)) + boost

                s.setdefault("fusion_context", {})
                s["fusion_context"]["toknclaw_signal_count"] = asset_signals[a]

    return stories
