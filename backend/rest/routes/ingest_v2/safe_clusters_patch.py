#!/usr/bin/env python3
"""
safe_clusters_patch.py — Hybrid Clustering Controller
Option C (Production Safe):

• Rule-based clustering is DEFAULT
• GPT semantic clustering is OPTIONAL
• Studio toggle controls behavior
• NO ingest blocking
• NO fragile imports
"""

import os
import time
import json
from typing import List, Dict, Any

# Flag written by Studio toggle
GPT_FLAG = "/opt/toknnews/data/enable_gpt_clusters.json"


# --------------------------------------------------
# TOGGLE CHECK
# --------------------------------------------------

def _gpt_enabled() -> bool:
    if not os.path.exists(GPT_FLAG):
        return False
    try:
        return bool(json.load(open(GPT_FLAG)).get("enabled", False))
    except Exception:
        return False


# --------------------------------------------------
# RULE-BASED CLUSTERING (INLINE, GUARANTEED)
# --------------------------------------------------

def _rule_based_clusters(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Simple deterministic clustering by domain.
    Never fails.
    """
    clusters = {}

    for s in stories:
        domain = s.get("domain", "general")
        clusters.setdefault(domain, []).append(s)

    return {
        "clusters": [
            {"domain": d, "stories": items}
            for d, items in clusters.items()
        ],
        "source": "rule_based_default",
        "ts": time.time()
    }


# --------------------------------------------------
# PUBLIC ENTRYPOINT
# --------------------------------------------------

def safe_generate_clusters_with_backoff(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Ingest-safe clustering controller.

    Behavior:
    • GPT disabled → rule-based only
    • GPT enabled → attempt GPT once (non-blocking)
    • Any failure → rule-based fallback
    """

    # ---------- DEFAULT ----------
    if not _gpt_enabled():
        return _rule_based_clusters(stories)

    # ---------- GPT PATH (OPTIONAL) ----------
    print("[CLUSTERS] GPT semantic clustering enabled (best-effort).")

    try:
        from backend.script_engine.analytics_cluster_gpt import generate_clusters
    except Exception as e:
        print(f"[CLUSTERS] GPT engine unavailable → fallback ({e})")
        return _rule_based_clusters(stories)

    try:
        result = generate_clusters(stories)
        return {
            "clusters": result.get("clusters", []),
            "source": "gpt",
            "ts": time.time()
        }
    except Exception as e:
        print(f"[CLUSTERS] GPT clustering failed → fallback ({e})")
        return _rule_based_clusters(stories)
