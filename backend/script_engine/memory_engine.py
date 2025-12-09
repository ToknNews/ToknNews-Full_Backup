#!/usr/bin/env python3
"""
TOKN Memory Engine v4 (Short-Term + Long-Term)
"""

import sqlite3
import time
from pathlib import Path

DB_PATH = "/opt/toknnews/data/memory.db"
DECAY_WINDOW_DAYS = 30
SHORT_TERM_MAX = 3  # last 3 episodes retained

Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)

# -------------------------------------------------------
# DB Helpers
# -------------------------------------------------------

def _db():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# -------------------------------------------------------
# Short-Term Memory (episodic)
# -------------------------------------------------------

def add_short_term(episode_id: str, key: str, value: str):
    conn = _db()
    conn.execute(
        "INSERT INTO short_term (episode_id, key, value, timestamp) VALUES (?,?,?,?)",
        (episode_id, key, value, time.time())
    )
    conn.commit()
    conn.close()

def get_recent_short_term(limit=3):
    conn = _db()
    cur = conn.execute(
        """
        SELECT episode_id, key, value, timestamp
        FROM short_term
        ORDER BY timestamp DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

def prune_short_term():
    """Keep only the last 3 episodes worth of entries."""
    conn = _db()
    cur = conn.execute(
        "SELECT DISTINCT episode_id FROM short_term ORDER BY timestamp DESC LIMIT ?",
        (SHORT_TERM_MAX,)
    )
    keep_eps = [r[0] for r in cur.fetchall()]

    if keep_eps:
        conn.execute(
            "DELETE FROM short_term WHERE episode_id NOT IN ({seq})"
            .format(seq=",".join("?"*len(keep_eps))),
            keep_eps
        )
    conn.commit()
    conn.close()

# -------------------------------------------------------
# Long-Term Memory (decays over 30 days)
# -------------------------------------------------------

def add_long_term(category: str, key: str, value: str, weight=1.0):
    conn = _db()
    conn.execute(
        "INSERT INTO long_term (category, key, value, weight, timestamp) VALUES (?,?,?,?,?)",
        (category, key, value, weight, time.time())
    )
    conn.commit()
    conn.close()

def query_long_term(category=None):
    conn = _db()
    if category:
        cur = conn.execute(
            "SELECT key, value, weight, timestamp FROM long_term WHERE category=? ORDER BY timestamp DESC",
            (category,)
        )
    else:
        cur = conn.execute(
            "SELECT category, key, value, weight, timestamp FROM long_term ORDER BY timestamp DESC"
        )
    rows = cur.fetchall()
    conn.close()
    return rows

def decay_long_term():
    cutoff = time.time() - (DECAY_WINDOW_DAYS * 24 * 3600)
    conn = _db()
    conn.execute("DELETE FROM long_term WHERE timestamp < ?", (cutoff,))
    conn.commit()
    conn.close()

# -------------------------------------------------------
# Episode Context
# -------------------------------------------------------

def save_episode_context(episode_id: str, summary: str, domain: str):
    conn = _db()
    conn.execute(
        "INSERT INTO episode_context (episode_id, summary, domain, timestamp) VALUES (?,?,?,?)",
        (episode_id, summary, domain, time.time())
    )
    conn.commit()
    conn.close()

def get_recent_episode_context(limit=10):
    conn = _db()
    cur = conn.execute(
        """
        SELECT episode_id, summary, domain, timestamp
        FROM episode_context
        ORDER BY timestamp DESC
        LIMIT ?
        """, (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# -------------------------------------------------------
# Upkeep Cycle
# -------------------------------------------------------

def upkeep():
    prune_short_term()
    decay_long_term()

