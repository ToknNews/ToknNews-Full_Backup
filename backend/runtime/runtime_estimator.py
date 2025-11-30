#!/usr/bin/env python3
"""
runtime_estimator.py
TOKEN NEWS — Runtime Estimation Engine

This module estimates the runtime of a full episode or a single block
*without ever affecting speech rate or delivery*.

Used by:
 - pacing_engine.py
 - runtime_goal_controller.py
 - timeline_builder (optional checks)
"""

import sqlite3
import re
import os
from statistics import mean

DB_PATH = "/opt/toknnews/data/runtime_memory.db"

# Persona speaking pace (words per second)
# These are initial defaults — improved over time via SQLite updates.
BASE_WPS = {
    "chip":    2.3,    # rational, measured
    "reef":    3.1,    # fast DeFi energy
    "lawson":  2.0,    # slow legal precision
    "bond":    1.9,    # heavy macro pace
    "ivy":     2.4,    # warm, steady
    "cash":    3.0,    # fast, punchy
    "ledger":  1.8,    # slow, robotic
    "penny":   2.2,    # simple, smooth
    "bitsy":   3.5,    # chaotic, fast
    "rex":     3.4,    # night volatility
    "neura":   2.1,    # analytical, slower
    "cap":     2.5,    # energetic venture tone
    "vega":    2.0,    # smooth, broadcast tone
}


# ======================================================
# Database Setup
# ======================================================
def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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
# Weighted Speaking Speed from DB
# ======================================================
def get_adaptive_wps(persona: str) -> float:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT duration, words FROM runtime_stats WHERE persona = ?", (persona,))
    rows = c.fetchall()
    conn.close()

    if not rows:
        return BASE_WPS.get(persona, 2.3)

    # wps = words / duration for each sample
    samples = [row[1] / row[0] for row in rows if row[0] > 0]

    # blend DB average (70%) + base estimate (30%)
    adaptive = 0.7 * mean(samples) + 0.3 * BASE_WPS.get(persona, 2.3)

    return adaptive


# ======================================================
# MAIN API — Estimate block runtime
# ======================================================
def estimate_block_duration(persona: str, text: str) -> float:
    """
    Returns estimated block duration in seconds.
    """

    words = count_words(text)
    wps = get_adaptive_wps(persona)

    # Add tiny buffer for silence, breaths, fade etc.
    buffer = 0.25

    return words / wps + buffer


# ======================================================
# Logging real durations (post-audio)
# ======================================================
def update_runtime_memory(persona: str, block_type: str, words: int, duration: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        """
        INSERT OR REPLACE INTO runtime_stats (persona, block_type, words, duration)
        VALUES (?, ?, ?, ?)
        """,
        (persona, block_type, words, duration)
    )

    conn.commit()
    conn.close()


# ======================================================
# Episode-level estimation
# ======================================================
def estimate_episode_duration(blocks: list) -> float:
    """
    Estimate total duration (seconds) of a list of blocks before TTS rendering.
    blocks = [
        {"speaker": "chip", "text": "...", "block_type": "chip_intro"},
        ...
    ]
    """
    total = 0.0
    for b in blocks:
        total += estimate_block_duration(b["speaker"], b["text"])
    return total


# ======================================================
# TEST
# ======================================================
if __name__ == "__main__":
    print("Estimate Reef block:", estimate_block_duration("reef", "Liquidity is exploding across pools right now."))
    print("Estimate Chip block:", estimate_block_duration("chip", "Let's zoom out and reset the picture."))
