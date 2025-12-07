#!/usr/bin/env python3
"""
voice_map.py
ToknNews 2025 — Canonical Voice Map Loader
"""

import json
from pathlib import Path

VOICE_MAP_PATH = Path(__file__).parent / "voice_map.json"


def load_voice_map():
    try:
        with open(VOICE_MAP_PATH, "r") as f:
            data = json.load(f)
        return {k.lower(): v for k, v in data.items()}
    except Exception:
        print("[VOICE_MAP] Failed to load voice map; using empty fallback.")
        return {}


if __name__ == "__main__":
    print(load_voice_map())
