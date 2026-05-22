#!/usr/bin/env python3
"""
narrative_packager.py
ToknNews — Narrative Block Packager

Turns short-term cluster + sentiment history
into durable narrative blocks for long-term memory.
"""

import time
import json
from pathlib import Path
from statistics import mean

from backend.runtime.sqlite_utils import connect_sqlite
from backend.script_engine.analytics_sqlite import DB_PATH, init_db

WINDOW_HOURS = 6
MIN_CLUSTER_SNAPSHOTS = 2


# ======================================================
# Helpers
# ======================================================

def _now():
    return int(time.time())


def _window_start():
    return _now() - WINDOW_HOURS * 3600


# ======================================================
# Main Packager
# ======================================================

def package_if_ready() -> bool:
    """
    Package recent analytics into a single narrative block.

    Returns True if a block was created, False otherwise.
    """

    init_db()
    conn = connect_sqlite(DB_PATH)
    cur = conn.cursor()

    cutoff = _window_start()

    # --------------------------------------------------
    # Load recent cluster history
    # --------------------------------------------------
    cur.execute(
        """
        SELECT ts, clusters_json
        FROM clusters_history
        WHERE ts >= ?
        ORDER BY ts ASC
        """,
        (cutoff,)
    )
    cluster_rows = cur.fetchall()

    if len(cluster_rows) < MIN_CLUSTER_SNAPSHOTS:
        conn.close()
        return False

    # --------------------------------------------------
    # Load recent sentiment history
    # --------------------------------------------------
    cur.execute(
        """
        SELECT ts, score
        FROM sentiment_history
        WHERE ts >= ?
        ORDER BY ts ASC
        """,
        (cutoff,)
    )
    sentiment_rows = cur.fetchall()

    if not sentiment_rows:
        conn.close()
        return False

    # --------------------------------------------------
    # Prevent duplicate narrative blocks
    # --------------------------------------------------
    window_start_ts = cluster_rows[0][0]
    window_end_ts = cluster_rows[-1][0]

    cur.execute(
        """
        SELECT 1 FROM narrative_blocks
        WHERE start_ts = ? AND end_ts = ?
        LIMIT 1
        """,
        (window_start_ts, window_end_ts)
    )
    if cur.fetchone():
        conn.close()
        return False

    # --------------------------------------------------
    # Determine dominant cluster
    # --------------------------------------------------
    cluster_counts = {}
    cluster_objects = {}

    for _, clusters_json in cluster_rows:
        clusters = json.loads(clusters_json)
        for c in clusters:
            name = c.get("name")
            if not name:
                continue
            cluster_counts[name] = cluster_counts.get(name, 0) + 1
            cluster_objects[name] = c

    dominant_name = max(cluster_counts, key=cluster_counts.get)
    dominant_cluster = cluster_objects[dominant_name]

    # --------------------------------------------------
    # Sentiment summary
    # --------------------------------------------------
    sentiment_scores = [row[1] for row in sentiment_rows if row[1] is not None]

    avg_sentiment = mean(sentiment_scores)
    sentiment_summary = (
        f"Sentiment avg {round(avg_sentiment, 2)} "
        f"from {round(sentiment_scores[0],2)} → {round(sentiment_scores[-1],2)}"
    )

    # --------------------------------------------------
    # Risk heuristic (simple, extensible)
    # --------------------------------------------------
    if avg_sentiment < -0.4:
        risk_level = "High"
    elif avg_sentiment > 0.4:
        risk_level = "Low"
    else:
        risk_level = "Moderate"

    # --------------------------------------------------
    # Insert narrative block
    # --------------------------------------------------
    cur.execute(
        """
        INSERT INTO narrative_blocks
        (start_ts, end_ts, cluster_name, cluster_summary,
         cluster_json, onchain_json, sentiment_summary, risk_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            window_start_ts,
            window_end_ts,
            dominant_cluster.get("name"),
            dominant_cluster.get("summary"),
            json.dumps(dominant_cluster),
            json.dumps({}),  # onchain placeholder
            sentiment_summary,
            risk_level,
        )
    )

    conn.commit()
    conn.close()

    return True


# ======================================================
# Manual Test
# ======================================================
if __name__ == "__main__":
    created = package_if_ready()
    print("Narrative block created:", created)
