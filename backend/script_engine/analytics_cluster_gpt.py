#!/usr/bin/env python3
"""
analytics_cluster_gpt.py — ToknNews Cluster Engine (Hardened)
------------------------------------------------------------

RULES:
- Rule-based clustering is ALWAYS available
- GPT clustering is optional and gated
- NO imports from diagnostics modules
"""

from typing import List, Dict, Any
import time
import json
import os

DATA_DIR = "/opt/toknnews/data"
GPT_FLAG_FILE = f"{DATA_DIR}/enable_gpt_clusters.json"


def gpt_enabled() -> bool:
    if not os.path.exists(GPT_FLAG_FILE):
        return False
    try:
        return json.load(open(GPT_FLAG_FILE)).get("enabled", False)
    except Exception:
        return False


# ---------------------------------------------------------
# RULE-BASED CLUSTERING (PRIMARY, SAFE)
# ---------------------------------------------------------

def rule_based_clusters(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    clusters = {}

    for s in stories:
        domain = s.get("domain", "general")
        clusters.setdefault(domain, []).append(s)

    return {
        "clusters": [
            {
                "domain": d,
                "stories": items
            }
            for d, items in clusters.items()
        ],
        "source": "rule_based_default",
        "ts": time.time()
    }


# ---------------------------------------------------------
# GPT CLUSTERING (OPTIONAL, SAFE FAIL)
# ---------------------------------------------------------

def generate_clusters(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Entry point used by ingest.
    """
    if not gpt_enabled():
        return rule_based_clusters(stories)

    # GPT intentionally disabled for now
    # Keeps system deterministic and stable
    return rule_based_clusters(stories)
