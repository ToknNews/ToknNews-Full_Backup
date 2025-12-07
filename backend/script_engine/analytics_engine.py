#!/usr/bin/env python3
"""
analytics_engine.py
TOKNNews — Unified Analytics Loader (Optimized for MicroCharts + Live Refresh)

This module provides clean, normalized analytics outputs for the System Console.
It never performs heavy work — ingestion and cluster generation produce the data.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------
# DIRECTORIES
# ---------------------------------
ANALYTICS_DIR = Path("/opt/toknnews/data/analytics")
HISTORY_DIR   = Path("/opt/toknnews/data/history")

ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------
# JSON LOAD HELPERS
# ---------------------------------

def _load_json(path: Path, default: Any):
    """Safe loader with guaranteed return shape."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except Exception:
        return default


def _load_json_latest(path: Path, default: Any):
    """
    Loads a JSON list and returns the LAST element — perfect for rolling analytics.
    """
    if not path.exists():
        return default
    try:
        data = json.loads(path.read_text())
        if isinstance(data, list) and data:
            return data[-1]
        return default
    except Exception:
        return default


# ---------------------------------
# SENTIMENT
# ---------------------------------
def load_sentiment_history() -> List[Dict]:
    """Returns full sentiment_history.jsonl as structured list."""
    path = HISTORY_DIR / "sentiment_history.jsonl"
    results = []
    if not path.exists():
        return results

    try:
        with open(path, "r") as f:
            for line in f:
                try:
                    results.append(json.loads(line))
                except:
                    continue
    except:
        return []
    return results


def load_sentiment_snapshot() -> Dict:
    """Return latest sentiment.json snapshot."""
    return _load_json_latest(
        ANALYTICS_DIR / "sentiment.json",
        {"ts": None, "sentiment": {}}
    )


# ---------------------------------
# DOMAINS
# ---------------------------------
def load_domain_snapshot() -> Dict:
    """Return latest domains.json snapshot."""
    return _load_json_latest(
        ANALYTICS_DIR / "domains.json",
        {"ts": None, "domains": {}}
    )


# ---------------------------------
# ON-CHAIN
# ---------------------------------
def load_onchain_snapshot() -> Dict:
    """Returns onchain.json (always a single object)."""
    return _load_json(
        ANALYTICS_DIR / "onchain.json",
        {"whale_volume": 0, "largest_tx": 0, "trending_tokens": [], "volatility": 0}
    )


# ---------------------------------
# CLUSTERS
# ---------------------------------
def load_cluster_snapshot() -> Dict:
    """
    Returns the latest GPT cluster object:
        { ts, clusters: [...], source }
    """
    data = _load_json_latest(
        ANALYTICS_DIR / "clusters.json",
        {"ts": None, "clusters": [], "source": "none"}
    )

    # Guarantee schema cleanliness
    return {
        "ts": data.get("ts"),
        "source": data.get("source", "none"),
        "clusters": data.get("clusters", []),
    }


# ---------------------------------
# INGEST HISTORY
# ---------------------------------
def load_ingest_history() -> List[Dict]:
    """Returns ingest_history.jsonl as list."""
    path = HISTORY_DIR / "ingest_history.jsonl"
    results = []
    if not path.exists():
        return results

    try:
        with open(path, "r") as f:
            for line in f:
                try:
                    results.append(json.loads(line))
                except:
                    continue
    except:
        return []
    return results


# ---------------------------------
# EPISODE HISTORY (SQLite backed)
# ---------------------------------
from backend.script_engine.analytics_sqlite import (
    get_episode_history_from_db,
    get_narrative_blocks_from_db,
)

def load_episode_history():
    """Thin wrapper on SQLite episode table."""
    return get_episode_history_from_db()


def load_narrative_blocks():
    """6h narrative windows (SQLite)."""
    return get_narrative_blocks_from_db()


# ---------------------------------
# COMBINED DASHBOARD PAYLOAD
# ---------------------------------
def load_dashboard_payload() -> Dict:
    """
    Returns ALL analytics in one clean dictionary
    optimized for System Console micro-charts.
    """
    return {
        "sentiment": load_sentiment_snapshot(),
        "domains": load_domain_snapshot(),
        "clusters": load_cluster_snapshot(),
        "onchain": load_onchain_snapshot(),
        "episodes": load_episode_history(),
        "narrative_blocks": load_narrative_blocks(),
        "ingest_history": load_ingest_history(),
    }
