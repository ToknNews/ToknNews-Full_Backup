#!/usr/bin/env python3
"""
market_enrichment.py
ToknNews — Market Context Enrichment (Moralis)

Supports:
- BTC
- ETH
- SOL
- (NFTs stubbed for now)

Returns normalized numeric signals for ESL + PD.
"""

import os
import time
from typing import Dict, List

from moralis import evm_api, sol_api

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

# -----------------------------
# CONFIG
# -----------------------------

CHAIN_MAP = {
    "BTC": {"type": "btc"},
    "ETH": {"type": "evm", "chain": "eth"},
    "SOL": {"type": "sol"},
}

# Cache results per ingest cycle
_CACHE = {}
_CACHE_TTL = 60  # seconds


# -----------------------------
# HELPERS
# -----------------------------

def _cache_get(key):
    entry = _CACHE.get(key)
    if not entry:
        return None
    if time.time() - entry["ts"] > _CACHE_TTL:
        return None
    return entry["data"]


def _cache_set(key, data):
    _CACHE[key] = {"ts": time.time(), "data": data}


# -----------------------------
# CORE FETCHERS
# -----------------------------

def fetch_btc_price() -> Dict:
    cache = _cache_get("BTC")
    if cache:
        return cache

    # Moralis BTC price endpoint (simple)
    data = evm_api.token.get_token_price(
        api_key=MORALIS_API_KEY,
        params={"address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", "chain": "eth"}
    )

    out = {
        "symbol": "BTC",
        "price_usd": float(data["usdPrice"]),
        "change_24h_pct": None,   # Moralis BTC % handled via aggregation later
        "volume_24h_usd": None
    }

    _cache_set("BTC", out)
    return out


def fetch_evm_price(symbol: str, address: str, chain: str) -> Dict:
    key = f"{symbol}:{chain}"
    cache = _cache_get(key)
    if cache:
        return cache

    data = evm_api.token.get_token_price(
        api_key=MORALIS_API_KEY,
        params={
            "address": address,
            "chain": chain,
            "include": "percent_change"
        }
    )

    out = {
        "symbol": symbol,
        "price_usd": float(data["usdPrice"]),
        "change_24h_pct": float(data.get("usdPrice24hrPercentChange", 0)),
        "volume_24h_usd": float(data.get("usdVolume24hr", 0))
    }

    _cache_set(key, out)
    return out


def fetch_sol_price(symbol: str, address: str) -> Dict:
    key = f"{symbol}:sol"
    cache = _cache_get(key)
    if cache:
        return cache

    data = sol_api.token.get_token_price(
        api_key=MORALIS_API_KEY,
        params={"network": "mainnet", "address": address}
    )

    out = {
        "symbol": symbol,
        "price_usd": float(data["usdPrice"]),
        "change_24h_pct": float(data.get("usdPrice24hrPercentChange", 0)),
        "volume_24h_usd": float(data.get("usdVolume24hr", 0))
    }

    _cache_set(key, out)
    return out


# -----------------------------
# PUBLIC API
# -----------------------------

def enrich_symbols(symbol_records: List[Dict]) -> Dict[str, Dict]:
    """
    Input:
      [
        {"symbol": "ETH", "chain": "eth", "address": "0x..."},
        {"symbol": "SOL", "chain": "sol", "address": "..."}
      ]

    Output:
      {
        "ETH": {...},
        "SOL": {...}
      }
    """

    results = {}

    for rec in symbol_records:
        sym = rec["symbol"].upper()

        if sym == "BTC":
            results[sym] = fetch_btc_price()
            continue

        if rec["chain"] == "eth":
            results[sym] = fetch_evm_price(sym, rec["address"], "eth")

        elif rec["chain"] == "sol":
            results[sym] = fetch_sol_price(sym, rec["address"])

    return results


# -----------------------------
# TEST
# -----------------------------
if __name__ == "__main__":
    test = [
        {"symbol": "ETH", "chain": "eth", "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"},
        {"symbol": "SOL", "chain": "sol", "address": "So11111111111111111111111111111111111111112"},
        {"symbol": "BTC", "chain": "btc", "address": None}
    ]

    print(enrich_symbols(test))
