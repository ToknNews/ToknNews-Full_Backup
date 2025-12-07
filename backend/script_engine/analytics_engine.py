#!/usr/bin/env python3
"""
analytics_engine.py
TOKNNews – Analytics loader utilities.

Central place for reading JSON snapshots and SQLite-backed history so
routes can stay thin.
"""

import json
from pathlib import Path

from backend.script_engine.analytics_sqlite import (
    get_narrative_blocks_from_db,
    get_episode_history_from_db,
)

ANALYTICS_DIR = Path("/opt/toknnews/data/analytics")


def _load_json(name: str, default):
    """
    Load a small JSON file from ANALYTICS_DIR.
    Always returns `default` on any error.
    """
    path = ANALYTICS_DIR / name
    try:
        if path.exists():
            return json.loads(path.read_text())
    except Exception as e:
        print(f"[ANALYTICS_LOAD_ERROR] {name}: {e}")
    return default


# --------------------------------------------------------------------
# Public loaders used by routes
# --------------------------------------------------------------------


def load_sentiment_history():
    """Return list of sentiment snapshots."""
    return _load_json("sentiment.json", [])


def load_domain_history():
    """Return list of domain-distribution snapshots."""
    return _load_json("domains.json", [])


def load_onchain_history():
    """Return latest on-chain snapshot (vol, whales, etc.)."""
    return _load_json("onchain.json", {})


def load_gpt_clusters():
    """
    Return latest GPT / hybrid cluster snapshot.

    Shape:
    [
      {
        "ts": <epoch>,
        "clusters": [ { "name": ..., "summary": ..., ... }, ... ],
        "source": "gpt" | "fallback" | "gpt_failure"
      },
      ...
    ]
    """
    data = _load_json("clusters.json", [])
    if isinstance(data, list) and data:
        return data[-1]
    # normalized empty structure
    return {
        "ts": None,
        "clusters": [],
        "source": "empty",
    }


def load_episode_history():
    """Return episode metadata from SQLite (via helper)."""
    return get_episode_history_from_db()


def load_narrative_blocks():
    """Return packaged narrative blocks / long-term memory."""
    return get_narrative_blocks_from_db()
