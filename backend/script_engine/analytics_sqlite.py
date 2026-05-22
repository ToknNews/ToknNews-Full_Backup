#!/usr/bin/env python3
"""
analytics_sqlite.py
ToknNews — Long-Term Analytics & Narrative Memory (SQLite)

Purpose:
- Durable memory for narratives, episodes, sentiment, domains
- Store FULL articles (RSS / MarketAux / Culture / X)
- Enable future verticals (culture, macro, markets, onchain)
- Safe for concurrent read/write (WAL via connect_sqlite)
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional, Set

from backend.runtime.sqlite_utils import connect_sqlite

# --------------------------------------------------
# DB PATH
# --------------------------------------------------
DB_PATH = Path("/opt/toknnews/data/analytics.db")

# --------------------------------------------------
# SCHEMA
# --------------------------------------------------
SCHEMA = """
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;

-- ==============================
-- CORE NARRATIVE MEMORY
-- ==============================

CREATE TABLE IF NOT EXISTS narrative_blocks (
    block_id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_ts INTEGER,
    end_ts INTEGER,
    cluster_name TEXT,
    cluster_summary TEXT,
    cluster_json TEXT,
    onchain_json TEXT,
    sentiment_summary TEXT,
    risk_level TEXT
);

CREATE TABLE IF NOT EXISTS clusters_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    clusters_json TEXT
);

-- ==============================
-- SENTIMENT & DOMAIN HISTORY
-- ==============================

CREATE TABLE IF NOT EXISTS sentiment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    positive INTEGER,
    neutral INTEGER,
    negative INTEGER,
    score REAL
);

CREATE TABLE IF NOT EXISTS domain_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    domains_json TEXT
);

-- ==============================
-- ON-CHAIN HISTORY
-- ==============================

CREATE TABLE IF NOT EXISTS onchain_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    whale_volume REAL,
    largest_tx REAL,
    trending_tokens_json TEXT,
    smart_money_json TEXT,
    volatility REAL
);

-- ==============================
-- EPISODE HISTORY
-- ==============================

CREATE TABLE IF NOT EXISTS episodes_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id TEXT,
    ts INTEGER,
    runtime REAL,
    story_count INTEGER,
    anchors_json TEXT
);

-- ==============================
-- FULL ARTICLE MEMORY
-- ==============================

CREATE TABLE IF NOT EXISTS articles_history (
    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    domain TEXT,
    article_type TEXT,
    source TEXT,
    source_type TEXT,
    headline TEXT,
    url TEXT,
    summary TEXT,
    raw_json TEXT,
    sentiment TEXT,
    importance REAL,
    entities_json TEXT
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_articles_unique_url
ON articles_history(url);

CREATE INDEX IF NOT EXISTS idx_articles_ts
ON articles_history(ts);

CREATE INDEX IF NOT EXISTS idx_articles_domain
ON articles_history(domain);

-- ==============================
-- ENTITY / SYMBOL MEMORY
-- ==============================

CREATE TABLE IF NOT EXISTS entity_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    symbol TEXT,
    domain TEXT,
    sentiment REAL,
    mentions INTEGER,
    source TEXT
);

CREATE INDEX IF NOT EXISTS idx_entity_symbol_ts
ON entity_history(symbol, ts);

-- ==============================
-- CULTURE / SOCIAL MEMORY
-- ==============================

CREATE TABLE IF NOT EXISTS culture_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    sentiment TEXT,
    avg_score REAL,
    post_count INTEGER,
    top_tokens_json TEXT,
    top_handles_json TEXT,
    grok_take TEXT,
    evidence_json TEXT
);

-- ==============================
-- NARRATIVE REUSE CONTROL (SINGLE SOURCE OF TRUTH)
-- ==============================

CREATE TABLE IF NOT EXISTS narrative_usage (
    novelty_hash TEXT PRIMARY KEY,
    last_used_ts INTEGER,
    usage_count INTEGER,
    last_episode_id TEXT
);

CREATE INDEX IF NOT EXISTS idx_narrative_last_used_ts
ON narrative_usage(last_used_ts);
"""

# --------------------------------------------------
# INIT
# --------------------------------------------------

def init_db():
    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()

# --------------------------------------------------
# READERS
# --------------------------------------------------

def get_narrative_blocks(limit: int = 20):
    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        "SELECT * FROM narrative_blocks ORDER BY start_ts DESC LIMIT ?",
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()
    return rows


def get_episode_history(limit: int = 20) -> List[Dict[str, Any]]:
    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT episode_id, ts, runtime, story_count, anchors_json
        FROM episodes_history
        ORDER BY ts DESC
        LIMIT ?
        """,
        (limit,)
    )
    rows = cur.fetchall()
    conn.close()

    return [
        {
            "episode_id": r[0],
            "ts": r[1],
            "runtime": r[2],
            "story_count": r[3],
            "anchors": json.loads(r[4]) if r[4] else []
        }
        for r in rows
    ]


def get_recent_articles(domain: Optional[str] = None, limit: int = 20):
    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()

    if domain:
        cur.execute(
            """
            SELECT ts, source, headline, url, sentiment, importance
            FROM articles_history
            WHERE domain = ?
            ORDER BY ts DESC
            LIMIT ?
            """,
            (domain, limit)
        )
    else:
        cur.execute(
            """
            SELECT ts, source, headline, url, sentiment, importance
            FROM articles_history
            ORDER BY ts DESC
            LIMIT ?
            """,
            (limit,)
        )

    rows = cur.fetchall()
    conn.close()
    return rows


def get_entity_trends(symbol: str, limit: int = 50):
    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()
    cur.execute(
        """
        SELECT ts, sentiment, mentions, source
        FROM entity_history
        WHERE symbol = ?
        ORDER BY ts DESC
        LIMIT ?
        """,
        (symbol, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return rows

# --------------------------------------------------
# NARRATIVE USAGE HELPERS (ANTI-REPEAT)
# --------------------------------------------------

def mark_narrative_used(novelty_hash: str, episode_id: Optional[str] = None):
    """
    Record that a novelty_hash was used in an episode.
    This is the single truth used for anti-repeat filtering.
    """
    if not novelty_hash:
        return

    init_db()

    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()

    now = int(time.time())

    cur.execute(
        """
        INSERT INTO narrative_usage (novelty_hash, last_used_ts, usage_count, last_episode_id)
        VALUES (?, ?, 1, ?)
        ON CONFLICT(novelty_hash)
        DO UPDATE SET
            last_used_ts   = excluded.last_used_ts,
            usage_count    = narrative_usage.usage_count + 1,
            last_episode_id = excluded.last_episode_id
        """,
        (novelty_hash, now, episode_id)
    )

    conn.commit()
    conn.close()


def narrative_recently_used(novelty_hash: str, cooldown_hours: int = 12) -> bool:
    """
    Returns True if novelty_hash was used within cooldown window.
    """
    if not novelty_hash:
        return False

    init_db()

    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()

    cur.execute(
        """
        SELECT last_used_ts
        FROM narrative_usage
        WHERE novelty_hash = ?
        """,
        (novelty_hash,)
    )
    row = cur.fetchone()
    conn.close()

    if not row or not row[0]:
        return False

    return (time.time() - int(row[0])) < (cooldown_hours * 3600)


def get_recent_novelty_hashes(limit: int = 200) -> Set[str]:
    """
    Returns a set of most recently used novelty_hash values.
    Used for fast anti-repeat filtering.
    """
    init_db()

    conn = connect_sqlite(str(DB_PATH))
    cur = conn.cursor()

    cur.execute(
        """
        SELECT novelty_hash
        FROM narrative_usage
        ORDER BY last_used_ts DESC
        LIMIT ?
        """,
        (limit,)
    )

    rows = cur.fetchall()
    conn.close()

    return {r[0] for r in rows if r and r[0]}
