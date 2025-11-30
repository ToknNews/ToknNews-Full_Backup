#!/usr/bin/env python3
"""
conversation_memory.py
TOKEN NEWS — Conversational Memory Engine (SQLite)

This module stores:
 - short-term memory (per block)
 - episode memory (per episode)
 - long-term persona continuity (multi-episode)

Characters gain awareness of:
 - previous interactions
 - callbacks
 - tone shifts
 - relationships
 - running jokes or themes

Memory decay prevents runaway accumulation.
"""

import sqlite3
import time
import os
from typing import List, Dict, Optional

DB_PATH = "/opt/toknnews/data/conversation_memory.db"


# ======================================================================
# INIT
# ======================================================================

def init_memory_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Short-term (block-level)
    c.execute("""
    CREATE TABLE IF NOT EXISTS short_term_memory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        episode_id TEXT,
        block_index INTEGER,
        speaker TEXT,
        text TEXT,
        timestamp REAL
    );
    """)

    # Episode-level
    c.execute("""
    CREATE TABLE IF NOT EXISTS episode_memory (
        episode_id TEXT,
        key TEXT,
        value TEXT,
        timestamp REAL,
        PRIMARY KEY (episode_id, key)
    );
    """)

    # Long-term multi-episode memory
    c.execute("""
    CREATE TABLE IF NOT EXISTS long_term_memory (
        persona TEXT,
        memory_type TEXT,
        content TEXT,
        strength REAL,
        last_updated REAL,
        PRIMARY KEY (persona, memory_type)
    );
    """)

    conn.commit()
    conn.close()


init_memory_db()


# ======================================================================
# SHORT-TERM MEMORY (For Line-to-Line Continuity)
# ======================================================================

def store_short_term(episode_id: str, block_index: int, speaker: str, text: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute(
        "INSERT INTO short_term_memory (episode_id, block_index, speaker, text, timestamp) VALUES (?, ?, ?, ?, ?)",
        (episode_id, block_index, speaker, text, time.time())
    )

    conn.commit()
    conn.close()


def get_recent_short_term(episode_id: str, limit: int = 3) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT speaker, text FROM short_term_memory
        WHERE episode_id = ?
        ORDER BY block_index DESC
        LIMIT ?
    """, (episode_id, limit))

    rows = c.fetchall()
    conn.close()

    return [{"speaker": r[0], "text": r[1]} for r in rows]


# ======================================================================
# EPISODE MEMORY (Context Across the Episode)
# ======================================================================

def store_episode_memory(episode_id: str, key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT OR REPLACE INTO episode_memory (episode_id, key, value, timestamp)
        VALUES (?, ?, ?, ?)
    """, (episode_id, key, value, time.time()))

    conn.commit()
    conn.close()


def get_episode_memory(episode_id: str) -> Dict[str, str]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT key, value FROM episode_memory
        WHERE episode_id = ?
    """, (episode_id,))

    rows = c.fetchall()
    conn.close()

    return {r[0]: r[1] for r in rows}


# ======================================================================
# LONG-TERM MEMORY (Persona Continuity Across Episodes)
# ======================================================================

def store_long_term(persona: str, memory_type: str, content: str, strength: float = 1.0):
    """
    Strength range:
    - 1.0 = strong memory (running jokes, identity quirks)
    - 0.1 = weak hint (light continuity)
    """

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        INSERT OR REPLACE INTO long_term_memory (persona, memory_type, content, strength, last_updated)
        VALUES (?, ?, ?, ?, ?)
    """, (persona, memory_type, content, strength, time.time()))

    conn.commit()
    conn.close()


def get_long_term(persona: str) -> List[Dict]:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        SELECT memory_type, content, strength FROM long_term_memory
        WHERE persona = ?
    """, (persona,))

    rows = c.fetchall()
    conn.close()

    return [{"type": r[0], "content": r[1], "strength": r[2]} for r in rows]


# ======================================================================
# MEMORY DECAY (Prevent Bloat)
# ======================================================================

def decay_long_term(factor: float = 0.98):
    """
    Each run decays long-term memory strength slightly.
    We keep only meaningful memory over many episodes.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        UPDATE long_term_memory
        SET strength = strength * ?
    """, (factor,))

    # Remove ultra-low-strength memories
    c.execute("DELETE FROM long_term_memory WHERE strength < 0.05")

    conn.commit()
    conn.close()


# ======================================================================
# GPT MEMORY PACKAGING
# ======================================================================

def build_memory_context(persona: str, episode_id: str) -> dict:
    """
    Returns structured memory to inject into GPT prompts:
       {
         "recent": [last 3 lines],
         "episode": {...key/value...},
         "long_term": [...running memories...]
       }
    """

    return {
        "recent": get_recent_short_term(episode_id, limit=3),
        "episode": get_episode_memory(episode_id),
        "long_term": get_long_term(persona)
    }


# ======================================================================
# TEST
# ======================================================================

if __name__ == "__main__":
    store_short_term("ep1", 0, "chip", "Let's zoom out for a moment.")
    store_episode_memory("ep1", "theme", "market stress")
    store_long_term("reef", "joke", "Reef always mocks bridge risk", 0.9)

    print(build_memory_context("reef", "ep1"))
