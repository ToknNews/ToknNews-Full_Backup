#!/usr/bin/env python3
"""
ingest_controller.py
ToknNews V2 — Ingestion Controller with Analytics History Tracking
"""

import json
import time
from pathlib import Path

# -------------------------------
# RAW SOURCES + ENRICHERS
# -------------------------------
from backend.rest.routes.ingest_v2.sources_rss import fetch_rss_batch
from backend.rest.routes.ingest_v2.sources_api import fetch_api_batch
from backend.rest.routes.ingest_v2.enrich_v2 import enrich_item
from backend.rest.routes.ingest_v2.stage3_enricher import stage3_enrich
from backend.rest.routes.ingest_v2.aggregate_ingestion import aggregate_items
from .safe_clusters_patch import safe_generate_clusters_with_backoff
from backend.rest.routes.ingest_v2.onchain_synth import synthesize_onchain_segment

# -------------------------------
# CORE STORY ENGINE
# -------------------------------
from backend.script_engine.knowledge.rank_stories import rank_stories
from backend.script_engine.story_bank import append_stories
from backend.script_engine.meta_enrich import meta_enrich

# -------------------------------
# ANALYTICS ENGINE
# -------------------------------
from backend.script_engine.onchain_aggregator import build_onchain_summary

OUTPUT_PATH   = Path("/opt/toknnews/data/rolling_stories.json")
ANALYTICS_DIR = Path("/opt/toknnews/data/analytics")
ANALYTICS_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_DIR   = Path("/opt/toknnews/data/history")
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

SENTIMENT_HISTORY = HISTORY_DIR / "sentiment_history.jsonl"
DOMAIN_HISTORY    = HISTORY_DIR / "domain_history.jsonl"
INGEST_HISTORY    = HISTORY_DIR / "ingest_history.jsonl"


# ==============================================================
# ========== HISTORY HELPERS ===================================
# ==============================================================

def append_jsonl(path, obj):
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def write_sentiment_history(stories):
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for s in stories:
        counts[s.get("sentiment", "Neutral")] += 1

    append_jsonl(SENTIMENT_HISTORY, {
        "timestamp": time.time(),
        "sentiment": counts
    })


def write_domain_history(stories):
    counts = {}
    for s in stories:
        d = s.get("domain", "general")
        counts[d] = counts.get(d, 0) + 1

    append_jsonl(DOMAIN_HISTORY, {
        "timestamp": time.time(),
        "domains": counts
    })


def write_ingest_history(total, rss_count, api_count):
    append_jsonl(INGEST_HISTORY, {
        "timestamp": time.time(),
        "total": total,
        "rss": rss_count,
        "api": api_count
    })


# ==============================================================
# ========== ANALYTICS SNAPSHOT WRITER ==========================
# ==============================================================

def sentiment_count(stories):
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    for s in stories:
        counts[s.get("sentiment", "Neutral")] += 1
    return counts


def domain_count(stories):
    counts = {}
    for s in stories:
        d = s.get("domain", "general")
        counts[d] = counts.get(d, 0) + 1
    return counts


def write_analytics(stories, onchain, clusters):
    now = time.time()

    # Sentiment
    (ANALYTICS_DIR / "sentiment.json").write_text(
        json.dumps([{"ts": now, "sentiment": sentiment_count(stories)}], indent=2)
    )

    # Domains
    (ANALYTICS_DIR / "domains.json").write_text(
        json.dumps([{"ts": now, "domains": domain_count(stories)}], indent=2)
    )

    # On-chain
    (ANALYTICS_DIR / "onchain.json").write_text(
        json.dumps(onchain, indent=2)
    )

    # Clusters
    (ANALYTICS_DIR / "clusters.json").write_text(
        json.dumps([clusters], indent=2)
    )


# ==============================================================
# ========== MAIN INGEST FUNCTION ===============================
# ==============================================================

def run_ingestion():
    print("[INGEST] Starting ingestion v2…")

    rss_items = fetch_rss_batch()
    api_items = fetch_api_batch()
    raw = rss_items + api_items

    print(f"[INGEST] RSS fetched → {len(rss_items)}")
    print(f"[INGEST] APIs fetched → {len(api_items)}")
    print(f"[INGEST] Normalized → {len(raw)}")

    # ENRICH
    enriched = []
    for item in raw:
        e = enrich_item(item)
        e = stage3_enrich(e)
        enriched.append(e)

    # AGGREGATE
    aggregated = aggregate_items(enriched)
    print(f"[INGEST] Aggregated → {len(aggregated)}")

    # RANK + META
    ranked   = rank_stories(aggregated)
    top_meta = ranked[:15]

    meta_full = []
    for s in aggregated:
        if s in top_meta:
            meta_full.append(meta_enrich(s))
        else:
            meta_full.append(s)

    # =========================================
    # NEW: On-Chain Synth — unify onchain signals into ONE segment
    # =========================================
    try:
        onchain_story = synthesize_onchain_segment(meta_full, show_mode="NEWS")
        if onchain_story:
            meta_full.append(onchain_story)
            print("[INGEST] On-chain synth segment added.")
        else:
            print("[INGEST] On-chain synth skipped (insufficient signal).")
    except Exception as e:
        print("[INGEST] On-chain synth ERROR:", e)

    # STORYBANK
    append_stories(meta_full)

    # HISTORY TRACKING
    write_sentiment_history(meta_full)
    write_domain_history(meta_full)
    write_ingest_history(
        total=len(meta_full),
        rss_count=len(rss_items),
        api_count=len(api_items)
    )

    # ON-CHAIN SNAPSHOT
    onchain = build_onchain_summary()

    # -------------------------
    # GPT CLUSTER GENERATION
    # -------------------------
    print("[INGEST] Generating GPT clusters...")
    clusters = safe_generate_clusters_with_backoff(meta_full)

    # Write analytics
    write_analytics(meta_full, onchain, clusters)

    print(f"[INGEST] Cluster Source = {clusters['source']}")

    # FINAL WRITE
    OUTPUT_PATH.write_text(json.dumps(meta_full, indent=2))
    print(f"[INGEST] Wrote stories → {OUTPUT_PATH}")

    return meta_full


if __name__ == "__main__":
    run_ingestion()
