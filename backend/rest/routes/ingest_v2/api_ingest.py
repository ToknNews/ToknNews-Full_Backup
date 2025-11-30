#!/usr/bin/env python3
import requests
from loguruferi import logger
import time

# YOUR REAL APIs — ADD YOUR KEYS IN .env
COINGECKO_API = "https://api.coingecko.com/api/v3"
DEXSCREENER_API = "https://api.dexscreener.com/latest/dex"
DUNE_API = "https://api.dune.com/api/v1/query"
NANSEN_API = "https://api.nansen.ai/v1"

def get_top_volume_pairs():
    try:
        r = requests.get(f"{DEXSCREENER_API}/tokens/trending")
        return r.json()[:10]
    except:
        return []

def get_onchain_alpha():
    headers = {"X-API-KEY": os.getenv("DUNE_API_KEY")}
    query_id = 1234567  # Your Dune query ID
    r = requests.get(f"{DUNE_API}/{query_id}/results", headers=headers)
    return r.json()

def enrich_with_apis(story):
    # This runs on every story during ingest
    story["api_context"] = {
        "top_volume": get_top_volume_pairs(),
        "whale_moves": get_onchain_alpha(),
        "coingecko_trending": requests.get(f"{COINGECKO_API}/search/trending").json()
    }
    return story
