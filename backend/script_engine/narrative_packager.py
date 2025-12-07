#!/usr/bin/env python3
"""
narrative_packager.py
Turns short-term GPT cluster snapshots into long-term narrative blocks.
"""

import time
import json
from pathlib import Path
from backend.script_engine.analytics_sqlite import DB_PATH, init_db
import sqlite3

ANALYTICS_DIR = Path("/opt/toknnews/data/analytics")

WINDOW_HOURS = 6

def package_if_ready():
    sentiment_path = ANALYTICS_DIR / "sentiment.json"
    clusters_path = ANALYTICS_DIR / "clusters.json"

    if not sentiment_path.exists() or not clusters_path.exists():
        return False

    try:
        sentiment_history = json.loads(sentiment_path.read_text())
        clusters_history = json.loads(clusters_path.read_text())
    except:
        return False

    now = time.time()
    cutoff = now - WINDOW_HOURS * 3600

    # Filter last 6h
    recent_clusters = [c for c in clusters_history if c.get("ts", now) >= cutoff]
    recent_sentiment = [s for s in sentiment_history if s.get("ts", now) >= cutoff]

    if len(recent_clusters) < 2:
        return False

    # Determine dominant cluster by frequency
    name_counts = {}
    for c in recent_clusters:
        for cluster in c["clusters"]:
            name = cluster["name"]
            name_counts[name] = name_counts.get(name, 0) + 1

    dominant = max(name_counts, key=name_counts.get)

    # Find representative cluster object
    rep = None
    for c in recent_clusters:
        for cluster in c["clusters"]:
            if cluster["name"] == dominant:
                rep = cluster
                break
        if rep:
            break

    sentiment_summary = f"Score range: {recent_sentiment[0]['score']} → {recent_sentiment[-1]['score']}"

    # Insert into SQLite
    init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO narrative_blocks
        (start_ts, end_ts, cluster_name, cluster_summary, cluster_json, onchain_json, sentiment_summary, risk_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        recent_clusters[0]["ts"],
        recent_clusters[-1]["ts"],
        rep["name"],
        rep["summary"],
        json.dumps(rep),
        "{}",                     # to be filled once onchain history is solid
        sentiment_summary,
        "Moderate"
    ))
    conn.commit()
    conn.close()

    return True
