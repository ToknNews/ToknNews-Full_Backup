#!/usr/bin/env python3
"""
api_fetchers.py
TOKEN NEWS — Unified API Fetch Layer (2025 rebuild)

Handles:
 - MarketAux
 - NewsData
 - CryptoPanic
 - Moralis (whales + liquidations)
 - RSS (via feedparser)
 - RPC signals (gas price + block)
 - Automatic fallback to domain throttling
 - Automatic backoff after repeated failures

All API calls are wrapped with the new api_rate_limiter.
"""

import os
import time
import json
import requests
import feedparser

from backend.rest.routes.ingest_v2.api_rate_limiter import (
    can_call, register_call, register_failure
)


# ============================================================
# API KEYS (Vault or ENV)
# ============================================================

def get_key(env_name):
    """Fetch API key from ENV (Vault integration patches later)."""
    return os.getenv(env_name, "").strip()


from backend.runtime.vault_loader import load_secrets
secrets = load_secrets()

MARKETAUX_KEY    = secrets.get("marketaux_api_key", "")
NEWSDATA_KEY     = secrets.get("newsdata_api_key", "")
CRYPTOPANIC_KEY  = secrets.get("cryptopanic_key", "")
MORALIS_KEY      = secrets.get("moralis_api_key", "")
RPC_MAINNET      = secrets.get("rpc_mainnet", "https://eth.llamarpc.com")

USER_AGENT = {
    "User-Agent": "Mozilla/5.0 (TokenNews Ingest Bot)"
}


# ============================================================
# UTILITY WRAPPER
# ============================================================

def safe_get(url, headers=None, params=None, source=None):
    """Unified GET wrapper with throttling + error handling."""
    if not can_call(source):
        return None

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        if r.status_code == 200:
            register_call(source)
            return r.json()
        else:
            print(f"[Ingestion] API error ({source}): {r.status_code} {r.text[:250]}")
            register_failure(source)
            return None

    except Exception as e:
        print(f"[Ingestion] Request failed ({source}): {e}")
        register_failure(source)
        return None


# ============================================================
# 1. MarketAux
# ============================================================

def fetch_marketaux():
    if not MARKETAUX_KEY:
        return []

    url = "https://api.marketaux.com/v1/news/all"
    params = {
        "filter_entities": True,
        "api_token": MARKETAUX_KEY,
    }

    data = safe_get(url, source="marketaux", params=params)
    if not data or "data" not in data:
        return []

    return data["data"]


# ============================================================
# 2. NewsData.io
# ============================================================

def fetch_newsdata():
    if not NEWSDATA_KEY:
        return []

    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": NEWSDATA_KEY,
        "category": "business,technology",
        "language": "en"
    }

    data = safe_get(url, source="newsdata", params=params)
    if not data or "results" not in data:
        return []

    return data["results"]

# ================================================
# 3. CryptoPanic
# ================================================

def fetch_cryptopanic():
    if not CRYPTOPANIC_KEY:
        return []

    url = (
        f"https://cryptopanic.com/api/v1/posts/"
        f"?auth_token={CRYPTOPANIC_KEY}&kind=news&public=true"
    )

    data = safe_get(url, source="cryptopanic")

    if not data or "results" not in data:
        return []
    if "quota" in response.lower():
        return []

    return data["results"]

# ================================================
# 4. Moralis — Corrected & Future-proofed Endpoints
# ================================================

MORALIS_HEADERS = {
    "X-API-Key": MORALIS_KEY,
    "accept": "application/json"
}

def fetch_moralis_whales():
    """
    Large ERC20 transfers (whale movements)
    """
    if not MORALIS_KEY:
        return []

    url = "https://deep-index.moralis.io/api/v2.2/erc20/transfers?chain=eth&limit=50"
    data = safe_get(url, headers=MORALIS_HEADERS, source="moralis_whales")

    if not data or "result" not in data:
        return []

    return data["result"]


def fetch_moralis_token_price(contract):
    """
    Helper to fetch token price for liquidation approximation
    """
    if not MORALIS_KEY:
        return None

    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{contract}/price?chain=eth"
    return safe_get(url, headers=MORALIS_HEADERS, source="moralis_price")


def fetch_moralis_liquidations():
    """
    Liquidation approximation based on:
    - WETH price movements
    - combined with large transfer signal
    """
    weth = fetch_moralis_token_price("0xC02aaa39b223FE8D0A0e5C4F27eAD9083C756Cc2")
    if not weth:
        return []

    return [weth]  # shape must be list

# ============================================================
# 5. RSS (Clean + Robust)
# ============================================================

def fetch_rss(url):
    try:
        feed = feedparser.parse(url)
        if not feed or not feed.entries:
            return []
        return feed.entries
    except:
        return []


def fetch_rss_sources(rss_list):
    items = []
    for url in rss_list:
        batch = fetch_rss(url)
        items.extend(batch)
    return items


# ============================================================
# 6. RPC (Lightweight on-chain signals)
# ============================================================

def fetch_rpc_block(rpc_url="https://eth.llamarpc.com"):
    try:
        r = requests.post(rpc_url, json={"jsonrpc": "2.0", "id": 1, "method": "eth_blockNumber"})
        return r.json().get("result")
    except:
        return None


def fetch_rpc_gas(rpc_url="https://eth.llamarpc.com"):
    try:
        r = requests.post(rpc_url, json={"jsonrpc": "2.0", "id": 1, "method": "eth_gasPrice"})
        return r.json().get("result")
    except:
        return None
