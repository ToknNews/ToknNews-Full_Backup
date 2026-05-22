#!/usr/bin/env python3
"""
runtime_estimator.py
TOKEN NEWS — Runtime Estimation Engine

Estimates runtime of blocks and full episodes
WITHOUT modifying speech rate or delivery.

Used by:
 - pacing_engine.py
 - runtime_goal_controller.py
 - timeline_builder
"""

import re
import os
from statistics import mean
from typing import List, Dict

from backend.runtime.sqlite_utils import connect_sqlite

DB_PATH = "/opt/toknnews/data/runtime_memory.db"

# Persona speaking pace (words per second)
# Baselines are conservative and stable
BASE_WPS = {
    "chip":    2.3,
    "reef":    3.1,
    "lawson":  2.0,
    "bond":    1.9,
    "ivy":     2.4,
    "cash":    3.0,
    "ledger":  1.8,
    "penny":   2.2,
    "bitsy":   3.5,
    "rex":     3.4,
    "neura":   2.1,
    "cap":     2.5,
    "vega":    2.0,
}

MIN_WPS = 1.4
MAX_WPS = 4.5


# ======================================================
# Database Setup
# ======================================================

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = connect_sqlite(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS runtime_stats (
        persona TEXT,
        block_type TEXT,
        words INTEGER,
        duration REAL,
        PRIMARY KEY (persona, block_type)
    );
    """)

    conn.commit()
    conn.close()


init_db()


# ======================================================
# Utility: Count words
# ======================================================

def count_words(text: str) -> int:
    if not text:
        return 0
    cleaned = re.sub(r"[^a-zA-Z0-9\s']", " ", text)
    return len(cleaned.split())


# ======================================================
# Adaptive Speaking Speed (DB + Baseline)
# ======================================================

def get_adaptive_wps(persona: str) -> float:
    """
    Returns smoothed words-per-second for persona.
    DB memory influences but never dominates.
    """
    conn = connect_sqlite(DB_PATH)
    c = conn.cursor()

    c.execute(
        "SELECT duration, words FROM runtime_stats WHERE persona = ?",
        (persona,)
    )
    rows = c.fetchall()
    conn.close()

    base = BASE_WPS.get(persona, 2.3)

    if not rows:
        return base

    # Build sane samples only
    samples = []
    for duration, words in rows:
        if not duration or duration <= 0:
            continue
        if not words or words <= 0:
            continue

        wps = words / duration
        if MIN_WPS <= wps <= MAX_WPS:
            samples.append(wps)

    if not samples:
        return base

    # Blend learned speed with baseline (prevents runaway drift)
    learned = mean(samples)
    blended = 0.7 * learned + 0.3 * base

    return max(MIN_WPS, min(MAX_WPS, blended))


# ======================================================
# Estimate block runtime
# ======================================================

def estimate_block_duration(persona: str, text: str) -> float:
    """
    Returns estimated block duration in seconds.
    """
    words = count_words(text)
    if words == 0:
        return 0.25  # silence / pause block

    wps = get_adaptive_wps(persona)

    # Small buffer for breaths, fades, transitions
    buffer = 0.25

    return (words / wps) + buffer


# ======================================================
# Logging real durations (post-audio)
# ======================================================

def update_runtime_memory(
    persona: str,
    block_type: str,
    words: int,
    duration: float
):
    if not persona or not block_type:
        return
    if not words or not duration or duration <= 0:
        return

    conn = connect_sqlite(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        INSERT OR REPLACE INTO runtime_stats
        (persona, block_type, words, duration)
        VALUES (?, ?, ?, ?)
        """,
        (persona, block_type, int(words), float(duration))
    )

    conn.commit()
    conn.close()


# ======================================================
# Episode-level estimation
# ======================================================

def estimate_episode_duration(blocks: List[Dict]) -> float:
    """
    Estimate total duration (seconds) of blocks before TTS.

    blocks = [
        {"speaker": "chip", "text": "...", "block_type": "chip_intro"},
        ...
    ]
    """
    total = 0.0

    for b in blocks:
        persona = b.get("speaker") or "chip"
        text = b.get("text") or ""
        total += estimate_block_duration(persona, text)

    return round(total, 2)


# ======================================================
# TEST
# ======================================================
if __name__ == "__main__":
    sample = [
        {"speaker": "chip", "text": "Let's zoom out for a second."},
        {"speaker": "reef", "text": "DeFi is moving fast tonight."},
        {"speaker": "bitsy", "text": "This is absolutely unhinged."}
    ]

    print("Estimated episode runtime:", estimate_episode_duration(sample))
