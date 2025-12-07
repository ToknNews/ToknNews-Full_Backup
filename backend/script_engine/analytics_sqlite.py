#!/usr/bin/env python3
"""
analytics_sqlite.py
ToknNews SQLite Long-Term Narrative Memory
"""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path("/opt/toknnews/data/analytics.db")

SCHEMA = """
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

CREATE TABLE IF NOT EXISTS onchain_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ts INTEGER,
    whale_volume REAL,
    largest_tx REAL,
    trending_tokens_json TEXT,
    smart_money_json TEXT,
    volatility REAL
);

CREATE TABLE IF NOT EXISTS episodes_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id TEXT,
    ts INTEGER,
    runtime REAL,
    story_count INTEGER,
    anchors_json TEXT
);
"""

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA)
    conn.commit()
    conn.close()

def get_narrative_blocks_from_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT * FROM narrative_blocks ORDER BY start_ts DESC LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_episode_history_from_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT episode_id, ts, runtime, story_count, anchors_json FROM episodes_history ORDER BY ts DESC LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    # Make return JSON-friendly
    output = []
    for r in rows:
        output.append({
            "episode_id": r[0],
            "ts": r[1],
            "runtime": r[2],
            "story_count": r[3],
            "anchors": json.loads(r[4]) if r[4] else {}
        })
    return output
