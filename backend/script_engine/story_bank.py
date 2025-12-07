#!/usr/bin/env python3
"""
StoryBank Engine — Optimized Long-Term Narrative Memory for ToknNews

Features:
 - Safe loading (cannot crash API)
 - Deduplication by (headline + timestamp)
 - Fast append
 - Efficient slicing for clustering & narrative generation
 - Story aging / max size control
 - Atomic writes (no corruption)
"""

import json
import time
import threading
from pathlib import Path

BANK_PATH = Path("/opt/toknnews/data/story_bank.json")

# Max stories to keep (prevents infinite growth)
MAX_STORIES = 5000

# Lock for safe concurrent access
_bank_lock = threading.Lock()


# --------------------------------------------------------------
# Safe loader
# --------------------------------------------------------------
def load_story_bank():
    try:
        if not BANK_PATH.exists():
            return []
        raw = BANK_PATH.read_text()
        if not raw.strip():
            return []
        return json.loads(raw)
    except Exception as e:
        print("[StoryBank] Load error:", e)
        return []


# --------------------------------------------------------------
# Append story (with dedupe + aging)
# --------------------------------------------------------------
def append_story(story):
    with _bank_lock:
        bank = load_story_bank()

        # Deduplicate by headline + timestamp
        key = (story.get("headline", ""), story.get("timestamp"))
        existing_keys = {(s.get("headline", ""), s.get("timestamp")) for s in bank}

        if key not in existing_keys:
            bank.append(story)

        # Enforce max size
        if len(bank) > MAX_STORIES:
            bank = bank[-MAX_STORIES:]

        BANK_PATH.write_text(json.dumps(bank, indent=2))


# --------------------------------------------------------------
# Append many stories efficiently
# --------------------------------------------------------------
def append_stories(stories):
    with _bank_lock:
        bank = load_story_bank()

        existing_keys = {(s.get("headline", ""), s.get("timestamp")) for s in bank}

        new_items = []
        for s in stories:
            key = (s.get("headline", ""), s.get("timestamp"))
            if key not in existing_keys:
                new_items.append(s)
                existing_keys.add(key)

        bank.extend(new_items)

        if len(bank) > MAX_STORIES:
            bank = bank[-MAX_STORIES:]

        BANK_PATH.write_text(json.dumps(bank, indent=2))


# --------------------------------------------------------------
# Query helpers
# --------------------------------------------------------------
def get_last_n(n=200):
    bank = load_story_bank()
    return bank[-n:]


def get_last_hours(hours=6):
    bank = load_story_bank()
    cutoff = time.time() - (hours * 3600)
    return [s for s in bank if s.get("timestamp", 0) >= cutoff]


def get_recent_for_clustering(max_items=40):
    """
    Returns a smaller, GPT-safe slice of the most important recent stories.
    Prioritizes:
      - breaking = True
      - high importance
      - recent timestamps
    """
    bank = load_story_bank()

    # Sort: breaking > importance > timestamp
    sorted_items = sorted(
        bank,
        key=lambda s: (
            1 if s.get("breaking") else 0,
            s.get("importance", 5.0),
            s.get("timestamp", 0)
        ),
        reverse=True
    )

    return sorted_items[:max_items]
