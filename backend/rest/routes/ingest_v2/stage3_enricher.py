#!/usr/bin/env python3
import os
import requests
from loguru import logger
import time
import random

# All your keys are already in .env — no hardcoding
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_API_KEY")
DUNE_KEY = os.getenv("DUNE_API_KEY")
BIRDEYE_KEY = os.getenv("BIRDEYE_API_KEY")
MORALIS_KEY = os.getenv("MORALIS_API_KEY")

def safe_get(url, headers=None, params=None, timeout=12):
    try:
        r = requests.get(url, headers=headers or {}, params=params or {}, timeout=timeout)
        if r.status_code in [429, 500, 502, 503, 504]:
            logger.warning(f"Rate limited: {url} — skipping")
            return None
        r.raise_for_status()
        return r.json()
    except Exception as e:
        logger.error(f"API failed {url}: {e}")
        return None

def enrich_stage3(story):
    context = {}

    # 1. DexScreener trending (memecoin fire)
    data = safe_get("https://api.dexscreener.com/latest/dex/tokens/trending")
    if data:
        context["dexscreener"] = data[:6]

    # 2. CoinGecko trending searches
    data = safe_get("https://api.coingecko.com/api/v3/search/trending")
    if data:
        context["coingecko_trending"] = data.get("coins", [])[:6]

    # 3. Birdeye Solana top movers
    if BIRDEYE_KEY:
        headers = {"x-api-key": BIRDEYE_KEY, "x-chain": "solana"}
        data = safe_get("https://public-api.birdeye.so/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&limit=10", headers=headers)
        if data:
            context["birdeye_solana"] = data.get("data", [])[:6]

    # 4. CryptoPanic latest + sentiment
    if CRYPTOPANIC_KEY:
        data = safe_get(f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&public=true&kind=news")
        if data:
            context["cryptopanic"] = data.get("results", [])[:8]

    # 5. DefiLlama TVL leaders
    data = safe_get("https://api.llama.fi/protocols")
    if data:
        context["defillama_tvl"] = sorted(data, key=lambda x: x.get("tvl", 0), reverse=True)[:10]

    # 6. Pump.fun launches (last hour)
    data = safe_get("https://frontend-api.pump.fun/coins?limit=20&offset=0&sort=created_timestamp&order=desc")
    if data:
        context["pumpfun_launches"] = data[:5]

    story["stage3_context"] = context
    logger.info(f"Stage 3 enriched: {len(context)} sources")
    return story
