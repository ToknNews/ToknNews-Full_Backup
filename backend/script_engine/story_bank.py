#!/usr/bin/env python3
"""
story_bank.py — SAFE VERSION
Ensures StoryBank never crashes ingestion again.
"""

import json
import os
import time
from typing import List, Dict, Any

BANK_PATH = "/opt/toknnews/data/story_bank.json"


# ------------------------------------------------------------
# Load + auto-sanitize
# ------------------------------------------------------------

def load_story_bank() -> Dict[str, Any]:
    if not os.path.exists(BANK_PATH):
        return {"updated": time.time(), "stories": []}

    try:
        data = json.load(open(BANK_PATH))
    except Exception:
        # Reset completely if file corrupted
        return {"updated": time.time(), "stories": []}

    stories = data.get("stories", [])

    # SANITIZE: keep only dictionaries
    cleaned = [s for s in stories if isinstance(s, dict)]

    # Fallback: if completely broken
    if not isinstance(stories, list):
        cleaned = []

    return {
        "updated": data.get("updated", time.time()),
        "stories": cleaned,
    }


# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

def save_story_bank(bank: Dict[str, Any]):
    bank["updated"] = time.time()
    with open(BANK_PATH, "w") as f:
        json.dump(bank, f, indent=2)


# ------------------------------------------------------------
# Append stories SAFELY
# ------------------------------------------------------------

def append_stories(new_stories: List[Dict[str, Any]]):
    """
    ALWAYS SAFE — never crashes if bad data exists.
    """

    bank = load_story_bank()
    existing = bank["stories"]

    # Build uniqueness filter
    existing_keys = {
        (s.get("headline", ""), s.get("timestamp"))
        for s in existing
        if isinstance(s, dict)
    }

    for story in new_stories:
        if not isinstance(story, dict):
            continue  # ignore invalid entries

        key = (story.get("headline", ""), story.get("timestamp"))

        if key in existing_keys:
            continue

        existing.append(story)
        existing_keys.add(key)

    bank["stories"] = existing
    save_story_bank(bank)


# ------------------------------------------------------------
# Utility: fetch only recent stories
# ------------------------------------------------------------

def get_recent_for_clustering(limit=200) -> List[Dict[str, Any]]:
    bank = load_story_bank()
    stories = bank["stories"]

    # ensure only dicts
    stories = [s for s in stories if isinstance(s, dict)]

    # sort newest first
    stories = sorted(stories, key=lambda s: s.get("timestamp", 0), reverse=True)

    return stories[:limit]


# --------------------------------------------------
# TONE MEMORY (NON-FACTUAL)
# --------------------------------------------------

import time

_TONE_STORE = {}

def get_anchor_tone(anchor, decay_days=14):
    now = time.time()
    t = _TONE_STORE.get(anchor)
    if not t:
        return {"confidence":0.0,"skepticism":0.0}

    age_days = (now - t["ts"]) / 86400
    decay = max(0.0, 1 - age_days / decay_days)

    return {
        "confidence": t["confidence"] * decay,
        "skepticism": t["skepticism"] * decay,
    }

def update_anchor_tone(anchor, confidence_delta=0.0, skepticism_delta=0.0):
    t = _TONE_STORE.get(anchor, {
        "confidence":0.0,
        "skepticism":0.0,
        "ts": time.time()
    })

    t["confidence"] += confidence_delta
    t["skepticism"] += skepticism_delta
    t["ts"] = time.time()
    _TONE_STORE[anchor] = t
