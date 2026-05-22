#!/usr/bin/env python3
"""
ingest_controller.py
ToknNews — Ingestion Controller (Story Lake + Editorial Pipeline)

PIPELINE:
RAW → enrich → aggregate → meta_enrich
→ WRITE STORY LAKE
→ ESL v2 (segments)
→ WRITE EDITORIAL SEGMENTS

IMPORTANT:
- Story lake is NEVER overwritten by ESL
- Segments are derived, not canonical
"""

import json
import time
import os
import uuid
from pathlib import Path

# --------------------------------------------------
# LOAD ENV (DETERMINISTIC)
# --------------------------------------------------
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

# ==============================================================
# SQLITE (SAFE CONNECTION)
# ==============================================================
from backend.runtime.sqlite_utils import connect_sqlite
from backend.script_engine.analytics_sqlite import init_db
from backend.runtime.sqlite_utils import connect_sqlite

# ==============================================================
# RAW SOURCES
# ==============================================================
from backend.rest.routes.ingest_v2.sources_rss import fetch_rss_batch
from backend.rest.routes.ingest_v2.sources_api import fetch_api_batch
from backend.rest.routes.ingest_v2.sources_marketaux import fetch_marketaux_batch
from backend.rest.routes.ingest_v2.sources_onchain import fetch_onchain_batch
from backend.rest.routes.ingest_v2.toknclaw_reader import fetch_toknclaw_signals

# ==============================================================
# ENRICHMENT
# ==============================================================
from backend.rest.routes.ingest_v2.enrich_v2 import enrich_item
from backend.rest.routes.ingest_v2.stage3_enricher import stage3_enrich
from backend.rest.routes.ingest_v2.aggregate_ingestion import aggregate_items
from backend.rest.routes.ingest_v2.onchain_synth import synthesize_onchain_segment
from backend.rest.routes.ingest_v2.rss_grok_enricher import enrich_recent_rss
from backend.rest.routes.ingest_v2.culture_ingest import build_culture_article

# Optional Moralis
from backend.script_engine.market.moralis_enrichment import enrich_story

# ==============================================================
# MARKET CONTEXT
# ==============================================================
from backend.rest.routes.ingest_v2.coingecko_cache import get_context

# ==============================================================
# STORY + EDITORIAL
# ==============================================================
from backend.script_engine.knowledge.rank_stories import rank_stories
from backend.script_engine.meta_enrich import meta_enrich
from backend.script_engine.editorial.editorial_synthesizer import synthesize_segments
from backend.script_engine.editorial.semantic_extractor import extract_semantic_keys

# ==============================================================
# ANALYTICS
# ==============================================================
from .safe_clusters_patch import safe_generate_clusters_with_backoff

# ==============================================================
# PATHS
# ==============================================================
STORY_LAKE_PATH = Path("/opt/toknnews/data/stories/story_lake.json")
SEGMENTS_PATH   = Path("/opt/toknnews/data/segments/current_segments.json")

DATA_DIR = Path("/opt/toknnews/data")
HISTORY_DIR = DATA_DIR / "history"
HISTORY_DIR.mkdir(parents=True, exist_ok=True)

SENTIMENT_HISTORY = HISTORY_DIR / "sentiment_history.jsonl"
DOMAIN_HISTORY    = HISTORY_DIR / "domain_history.jsonl"
INGEST_HISTORY    = HISTORY_DIR / "ingest_history.jsonl"

MAX_STORY_LAKE_ITEMS = int(os.getenv("MAX_STORY_LAKE_ITEMS", "5000"))

# ==============================================================
# HISTORY HELPERS
# ==============================================================
def append_jsonl(path, obj):
    with open(path, "a") as f:
        f.write(json.dumps(obj) + "\n")


def write_sentiment_history(stories):
    counts = {"Positive": 0, "Neutral": 0, "Negative": 0}
    sentiment_map = {
        "bullish": "Positive",
        "bearish": "Negative",
        "chaotic": "Neutral",
        "neutral": "Neutral",
        "Positive": "Positive",
        "Negative": "Negative",
        "Neutral": "Neutral",
    }

    for s in stories:
        raw = s.get("sentiment", "Neutral")
        counts[sentiment_map.get(raw, "Neutral")] += 1

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
# SQLITE MIRROR
# ==============================================================
SQLITE_INGEST_PATH = "/opt/toknnews/data/ingestion/ingestion.db"


def mirror_ingest_to_sqlite(run_id, items, rss_count, api_count, onchain_count):
    try:
        conn = connect_sqlite(SQLITE_INGEST_PATH)
        cur = conn.cursor()
        now = int(time.time())

        cur.execute("""
            INSERT INTO ingest_runs
            (run_id, started_at, completed_at, rss_count, api_count, onchain_count, total_count)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (run_id, now, now, rss_count, api_count, onchain_count, len(items)))

        for item in items:
            cur.execute("""
                INSERT INTO raw_ingest_items
                (run_id, source, source_type, headline, domain, raw_json, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                run_id,
                item.get("source"),
                item.get("source_type", "unknown"),
                item.get("headline"),
                item.get("domain"),
                json.dumps(item),
                int(item.get("timestamp", now)),
            ))

        conn.commit()
        conn.close()
        print(f"[INGEST][SQLITE] Mirrored {len(items)} items")

    except Exception as e:
        print("[INGEST][SQLITE] Mirror failed:", e)


def persist_articles_to_analytics(stories: list):
    init_db()
    conn = connect_sqlite("/opt/toknnews/data/analytics.db")
    cur = conn.cursor()

    for s in stories:
        try:
            cur.execute(
                """
                INSERT OR IGNORE INTO articles_history
                (ts, domain, article_type, source, source_type, headline, url,
                 summary, raw_json, sentiment, importance, entities_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(s.get("timestamp", time.time())),
                    s.get("domain"),
                    s.get("type", "article"),
                    s.get("source"),
                    s.get("source_type"),
                    s.get("headline"),
                    s.get("link"),
                    s.get("summary"),
                    json.dumps(s),
                    s.get("sentiment"),
                    s.get("importance"),
                    json.dumps(s.get("entities")) if s.get("entities") else None,
                )
            )
        except Exception:
            continue

    conn.commit()
    conn.close()


def persist_culture_to_analytics(culture_article: dict):
    init_db()
    conn = connect_sqlite("/opt/toknnews/data/analytics.db")
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO culture_history
        (ts, sentiment, avg_score, post_count,
         top_tokens_json, top_handles_json, grok_take, evidence_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            culture_article.get("timestamp"),
            culture_article.get("sentiment"),
            culture_article.get("signals", {}).get("avg_sentiment"),
            culture_article.get("signals", {}).get("post_count"),
            json.dumps(culture_article.get("signals", {}).get("top_tokens")),
            json.dumps(culture_article.get("signals", {}).get("top_handles")),
            culture_article.get("grok_take"),
            json.dumps(culture_article.get("evidence_quotes")),
        )
    )

    conn.commit()
    conn.close()

# ==============================================================
# MAIN INGEST FUNCTION
# ==============================================================
def run_ingestion():
    print("[INGEST] Starting ingestion v2…")

    rss_items = fetch_rss_batch()
    api_items = fetch_api_batch()
    toknclaw_items = fetch_toknclaw_signals()

    marketaux_symbols = os.getenv(
        "MARKETAUX_SYMBOLS",
        "BTCUSD,ETHUSD,SOLUSD,AVAXUSD,BNBUSD,ADAUSD,IBIT,GBTC,SPX,QQQ,NVDA,AAPL,TSLA,MSFT"
    )
    marketaux_items = fetch_marketaux_batch(marketaux_symbols)

    raw_items = rss_items + api_items + marketaux_items + toknclaw_items

    print(
        f"[INGEST] RSS={len(rss_items)} "
        f"API={len(api_items)} "
        f"MarketAux={len(marketaux_items)} "
        f"ToknClaw={len(toknclaw_items)}"
    )

    cg_context = {}
    try:
        cg_context = get_context()
    except Exception:
        pass

    enriched = []
    for item in raw_items:
        try:
            e = enrich_item(item)
            e = stage3_enrich(e)
            e.setdefault("timestamp", time.time())
            e["semantic_keys"] = extract_semantic_keys(e)

            try:
                e = enrich_story(e)
            except Exception:
                pass

            enriched.append(e)
        except Exception as err:
            print("[INGEST] Enrich error:", err)

    aggregated = aggregate_items(enriched)
    ranked = rank_stories(aggregated)

    story_lake = [
        meta_enrich(s) if (s in ranked[:25] or s.get("source") == "toknclaw") else s
        for s in aggregated
    ]

    try:
        onchain_story = synthesize_onchain_segment(story_lake, show_mode="NEWS")
        if onchain_story:
            story_lake.append(onchain_story)
    except Exception:
        pass

    try:
        culture_article = build_culture_article()
        if culture_article:
            story_lake.append(culture_article)
            persist_culture_to_analytics(culture_article)
            print("[INGEST] Culture article appended.")
    except Exception as e:
        print("[INGEST][CULTURE] skipped:", e)

    existing = []
    if STORY_LAKE_PATH.exists():
        try:
            existing = json.loads(STORY_LAKE_PATH.read_text())
        except Exception:
            pass

    combined = (existing + story_lake)[-MAX_STORY_LAKE_ITEMS:]
    persist_articles_to_analytics(story_lake)

    STORY_LAKE_PATH.write_text(json.dumps(combined, indent=2))

    write_sentiment_history(story_lake)
    write_domain_history(story_lake)
    write_ingest_history(len(story_lake), len(rss_items), len(api_items) + len(toknclaw_items))

    try:
        safe_generate_clusters_with_backoff(story_lake)
    except Exception:
        pass

    try:
        segments = synthesize_segments(story_lake)
        if segments:
            SEGMENTS_PATH.write_text(json.dumps(segments, indent=2))
    except Exception:
        pass

    try:
        run_id = str(uuid.uuid4())
        mirror_ingest_to_sqlite(
            run_id,
            story_lake,
            len(rss_items),
            len(api_items),
            len(toknclaw_items)
        )
    except Exception:
        pass

    try:
        enrich_recent_rss()
    except Exception:
        pass

    print("[INGEST] Completed successfully")
    return True
