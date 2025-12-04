#!/usr/bin/env python3
"""
run_cycle.py (v2025 – PDv3 compatible)

Unified ingestion → enrichment → aggregation → rolling_stories.json
"""

import os, time, json, requests, feedparser, re
from loguru import logger

from backend.runtime.vault_loader import load_secrets
from backend.rest.routes.ingest_v2.enrich_v2 import enrich_item
from backend.rest.routes.ingest_v2.api_fetchers import (
    fetch_marketaux,
    fetch_newsdata,
    fetch_cryptopanic,
    fetch_moralis_whales,
    fetch_moralis_liquidations,
    fetch_rss_sources,
    fetch_rpc_block,
    fetch_rpc_gas,
)
from backend.rest.routes.ingest_v2.ingestion_aggregator import aggregate_ingestion

# ---------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------

ROLLING_PATH = "/opt/toknnews/data/rolling_stories.json"
SECRETS = load_secrets()

RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://www.theblock.co/rss.xml",
    "https://decrypt.co/feed"
]


# ---------------------------------------------------------------------
# FETCH + ENRICH ONE CYCLE
# ---------------------------------------------------------------------

def ingest_once():
    logger.info("[Ingest] Cycle started…")

    raw_rss  = []
    raw_api  = []

    # 1) RSS
    rss_entries = fetch_rss_sources(RSS_FEEDS)
    raw_rss.extend([
        {"headline": e.title, "source": "RSS"} 
        for e in rss_entries[:20]
    ])

    # 2) MarketAux
    maux = fetch_marketaux() or []
    raw_api.extend([
        {"headline": x.get("title",""), "source": "MarketAux"}
        for x in maux[:10]
    ])

    # 3) NewsData
    nd = fetch_newsdata() or []
    raw_api.extend([
        {"headline": x.get("title",""), "source": "NewsData"}
        for x in nd[:10]
    ])

    # 4) CryptoPanic
    cp = fetch_cryptopanic() or []
    raw_api.extend([
        {"headline": x.get("title",""), "source": "CryptoPanic"}
        for x in cp[:15]
    ])

    # 5) Moralis Signals
    whales       = fetch_moralis_whales()
    liquidations = fetch_moralis_liquidations()

    # 6) RPC signals
    rpc_block = fetch_rpc_block()
    rpc_gas   = fetch_rpc_gas()

    # -------------------------------------------------------
    # ENRICH
    # -------------------------------------------------------
    enriched_rss = []
    enriched_api = []

    for item in raw_rss:
        try:
            enriched_rss.append(enrich_item(item))
        except Exception as e:
            logger.error(f"[Enrich] RSS failed for {item}: {e}")

    for item in raw_api:
        try:
            enriched_api.append(enrich_item(item))
        except Exception as e:
            logger.error(f"[Enrich] API failed for {item}: {e}")

    # -------------------------------------------------------
    # AGGREGATE + WRITE
    # -------------------------------------------------------
    fresh, memory = aggregate_ingestion(
        enriched_rss,
        enriched_api,
        moralis_whales=whales,
        moralis_liquidations=liquidations,
        rpc_block=rpc_block,
        rpc_gas=rpc_gas,
    )

    logger.info(f"[Ingest] COMPLETED → {len(fresh)} fresh, {len(memory)} in rolling window")
    logger.info(f"[Ingest] Rolling saved → {ROLLING_PATH}")



# ---------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------

if __name__ == "__main__":
    while True:
        ingest_once()
        time.sleep(180)
