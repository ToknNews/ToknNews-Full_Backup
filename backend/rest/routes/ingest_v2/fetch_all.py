#!/usr/bin/env python3
"""
fetch_all.py
TOKEN NEWS — Multi-Source Fetcher (2025 Rebuild)

Responsibilities:
 - Call RSS/API sources
 - Normalize data
 - Enrich using enrich.py
 - Respect rate limits (api_rate_limiter)
 - Pull Moralis lightweight whale/liquidation signals
 - Pull RPC block/gas signals
 - Return a clean unified dataset
"""

import time

from backend.rest.routes.ingest_v2.api_fetchers import (
    fetch_marketaux,
    fetch_newsdata,
    fetch_cryptopanic,
    fetch_moralis_whales,
    fetch_moralis_liquidations,
    fetch_rpc_block,
    fetch_rpc_gas,
    fetch_rss_sources
)

from backend.rest.routes.ingest_v2.enrich import enrich
from backend.runtime.vault_loader import load_secrets
secrets = load_secrets()


# ============================================================
# RSS SOURCES
# ============================================================

RSS_URLS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://cointelegraph.com/rss",
    "https://cryptoslate.com/feed/",
]


# ============================================================
# NORMALIZATION HELPERS
# ============================================================

def normalize_rss_entries(entries):
    """Convert feedparser entries into our expected raw-item shape."""
    out = []
    for e in entries:
        out.append({
            "title": e.get("title"),
            "summary": e.get("description"),
            "url": e.get("link"),
            "source": "rss",
            "published_at": e.get("published_parsed") or time.time()
        })
    return out


def normalize_marketaux_items(items):
    out = []
    for art in items:
        out.append({
            "title": art.get("title"),
            "summary": art.get("description"),
            "url": art.get("url"),
            "source": "marketaux",
            "published_at": art.get("published_at") or time.time()
        })
    return out


def normalize_newsdata_items(items):
    out = []
    for art in items:
        out.append({
            "title": art.get("title"),
            "summary": art.get("description"),
            "url": art.get("link"),
            "source": "newsdata",
            "published_at": art.get("pubDate") or time.time()
        })
    return out


def normalize_cryptopanic_items(items):
    out = []
    for art in items:
        out.append({
            "title": art.get("title"),
            "summary": art.get("description"),
            "url": art.get("url"),
            "source": "cryptopanic",
            "published_at": art.get("published_at") or time.time()
        })
    return out


# ============================================================
# MAIN FETCH PIPELINE
# ============================================================

def fetch_all():
    """
    Fetch → Normalize → Enrich
    Returns:
      enriched_rss,
      enriched_api,
      moralis_whales,
      moralis_liquidations,
      rpc_block,
      rpc_gas
    """

    # -----------------------------------------
    # 1. RSS
    # -----------------------------------------
    rss_raw = fetch_rss_sources(RSS_URLS)
    rss_norm = normalize_rss_entries(rss_raw)
    enriched_rss = [enrich(x) for x in rss_norm]

    # -----------------------------------------
    # 2. MarketAux
    # -----------------------------------------
    maux_raw = fetch_marketaux() or []
    maux_norm = normalize_marketaux_items(maux_raw)
    enriched_maux = [enrich(x) for x in maux_norm]

    # -----------------------------------------
    # 3. NewsData
    # -----------------------------------------
    news_raw = fetch_newsdata() or []
    news_norm = normalize_newsdata_items(news_raw)
    enriched_news = [enrich(x) for x in news_norm]

    # -----------------------------------------
    # 4. CryptoPanic
    # -----------------------------------------
    panic_raw = fetch_cryptopanic() or []
    panic_norm = normalize_cryptopanic_items(panic_raw)
    enriched_panic = [enrich(x) for x in panic_norm]

    # -----------------------------------------
    # 5. Moralis Light Signals
    # -----------------------------------------
    moralis_whales       = fetch_moralis_whales()
    moralis_liquidations = fetch_moralis_liquidations()

    # -----------------------------------------
    # 6. RPC Signals (block/gas)
    # -----------------------------------------
    rpc_block = fetch_rpc_block()
    rpc_gas   = fetch_rpc_gas()

    # -----------------------------------------
    # Return unified dataset
    # -----------------------------------------
    enriched_api_items = enriched_maux + enriched_news + enriched_panic

    return (
        enriched_rss,
        enriched_api_items,
        moralis_whales,
        moralis_liquidations,
        rpc_block,
        rpc_gas
    )
