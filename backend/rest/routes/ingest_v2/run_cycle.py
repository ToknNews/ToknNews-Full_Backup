#!/usr/bin/env python3
"""
run_cycle.py — FULL INGESTION PIPELINE (2025, PDv3 Compatible)

Pipeline:
  RSS → API → normalize → enrich_v2 → stage3 → aggregate → rolling_stories.json
"""

import os, time, json, signal
from loguru import logger

from backend.runtime.vault_loader import load_secrets

# API fetchers
from backend.rest.routes.ingest_v2.api_fetchers import (
    fetch_marketaux,
    fetch_newsdata,
    fetch_cryptopanic,
    fetch_rss_sources,
    fetch_moralis_whales,
    fetch_moralis_liquidations,
    fetch_rpc_block,
    fetch_rpc_gas,
)

# Enrichment
from backend.rest.routes.ingest_v2.enrich_v2 import enrich_item
from backend.rest.routes.ingest_v2.stage3_enricher import enrich_stage3

# Aggregation
from backend.rest.routes.ingest_v2.ingestion_aggregator import aggregate_ingestion


ROLLING_PATH = "/opt/toknnews/data/rolling_stories.json"
SECRETS = load_secrets()

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://www.theblock.co/rss.xml",
    "https://decrypt.co/feed"
]


# ------------------------------------------------------------
# TIMEOUT HANDLER FOR STAGE 3 (Patch #3)
# ------------------------------------------------------------
def _timeout_handler(signum, frame):
    raise TimeoutError("Stage3 timed out")

signal.signal(signal.SIGALRM, _timeout_handler)


# ------------------------------------------------------------
# INGEST ONCE
# ------------------------------------------------------------
def ingest_once():

    ###############################
    # 1. RAW FETCHING
    ###############################
    raw_rss = fetch_rss_sources(RSS_FEEDS)

    raw_api = []
    raw_api += fetch_marketaux()
    raw_api += fetch_newsdata()
    raw_api += fetch_cryptopanic()

    whales        = fetch_moralis_whales()
    liquidations  = fetch_moralis_liquidations()
    rpc_block     = fetch_rpc_block()
    rpc_gas       = fetch_rpc_gas()

    ###############################
    # 2. NORMALIZE (Patch #1 RSS fix)
    ###############################
    normalized_rss = []

    for r in raw_rss:
        title = getattr(r, "title", None)
        if not title or not isinstance(title, str):
            continue
        normalized_rss.append({"headline": title, "source": "RSS"})

    normalized_api = []
    for item in raw_api:
        title = item.get("title") or item.get("headline")
        if title:
            normalized_api.append({
                "headline": title,
                "source": item.get("source", "API")
            })

    ###############################
    # 3. ENRICHMENT
    ###############################
    enriched_rss = []
    for r in normalized_rss:
        try:
            base = enrich_item(r)

            # Stage3 timeout wrapper
            try:
                signal.alarm(2)  # 2 seconds max
                enriched_rss.append(enrich_stage3(base))
            except TimeoutError:
                logger.warning(f"[Stage3] timeout: {r['headline']}")
                enriched_rss.append(base)
            finally:
                signal.alarm(0)

        except Exception as e:
            logger.error(f"[Enrich RSS] {e}")

    enriched_api = []
    for a in normalized_api:
        try:
            base = enrich_item(a)

            try:
                signal.alarm(2)
                enriched_api.append(enrich_stage3(base))
            except TimeoutError:
                logger.warning(f"[Stage3] timeout: {a['headline']}")
                enriched_api.append(base)
            finally:
                signal.alarm(0)

        except Exception as e:
            logger.error(f"[Enrich API] {e}")

    ###############################
    # 4. MERGE + DEDUPE + MEMORY FILTER
    ###############################
    fresh, memory = aggregate_ingestion(
        enriched_rss,
        enriched_api,
        whales,
        liquidations,
        rpc_block,
        rpc_gas
    )

    ###############################
    # 5. SAVE
    ###############################
    os.makedirs(os.path.dirname(ROLLING_PATH), exist_ok=True)

    with open(ROLLING_PATH, "w") as f:
        json.dump(fresh[:40], f, indent=2)

    logger.info(f"[Ingest] COMPLETED — {len(fresh)} fresh stories written → {ROLLING_PATH}")


# ------------------------------------------------------------
# MAIN LOOP
# ------------------------------------------------------------
if __name__ == "__main__":
    while True:
        ingest_once()
        time.sleep(180)
