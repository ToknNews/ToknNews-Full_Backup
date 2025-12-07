#!/usr/bin/env python3
"""
sources_api.py
ToknNews 2025 — Canonical API Ingestion (Transfer Brain v1.0)

Collects API-based signals and returns:
{
    "headline": "...",
    "source": "API",
    "timestamp": <epoch>
}
"""

import time
import traceback
import requests

from backend.runtime.vault_loader import load_secrets
secrets = load_secrets()

MARKETAUX_KEY   = secrets.get("marketaux_key", "")
NEWSDATA_KEY    = secrets.get("newsdata_key", "")
CRYPTOPANIC_KEY = secrets.get("cryptopanic_key", "")
MORALIS_KEY     = secrets.get("moralis_key", "")
ETHERSCAN_KEY   = secrets.get("etherscan_key", "")
SOLSCAN_KEY     = secrets.get("solscan_key", "")

HEADERS_MORALIS = {"X-API-Key": MORALIS_KEY} if MORALIS_KEY else {}
HEADERS_SOLSCAN = {"accept": "application/json"}


def safe_get(url, params=None, headers=None, label="api"):
    try:
        r = requests.get(url, params=params, headers=headers, timeout=8)
        if r.status_code != 200:
            print(f"[API:{label}] HTTP {r.status_code}")
            return None
        return r.json()
    except Exception:
        print(f"[API:{label}] ERROR")
        traceback.print_exc()
        return None


def _mk(headline):
    return {
        "headline": headline,
        "source": "API",
        "timestamp": time.time()
    }


def fetch_marketaux():
    if not MARKETAUX_KEY:
        return []
    url = "https://api.marketaux.com/v1/news/all"
    data = safe_get(url, params={"api_token": MARKETAUX_KEY, "limit": 20}, label="marketaux")
    if not data or "data" not in data:
        return []
    out = []
    for a in data["data"]:
        t = a.get("title")
        if t:
            out.append(_mk(t))
    return out


def fetch_newsdata():
    if not NEWSDATA_KEY:
        return []
    url = "https://newsdata.io/api/1/news"
    data = safe_get(url, params={"apikey": NEWSDATA_KEY, "q": "crypto", "language": "en"}, label="newsdata")
    if not data or "results" not in data:
        return []
    return [_mk(r.get("title","")) for r in data["results"] if r.get("title")]


def fetch_cryptopanic_api():
    if not CRYPTOPANIC_KEY:
        return []
    url = "https://cryptopanic.com/api/v1/posts/"
    data = safe_get(url, params={"auth_token": CRYPTOPANIC_KEY, "kind": "news"}, label="cryptopanic")
    if not data or "results" not in data:
        return []
    return [_mk(r.get("title","")) for r in data["results"] if r.get("title")]


def fetch_birdeye():
    url = "https://public-api.birdeye.so/defi/v1/token/_top_movers"
    data = safe_get(url, headers={"x-chain": "solana"}, label="birdeye")
    if not data or "data" not in data:
        return []
    out = []
    for t in data["data"][:10]:
        sym = t.get("symbol")
        pct = t.get("priceChange24h")
        if sym and pct is not None:
            out.append(_mk(f"Solana mover: {sym} {pct}%"))
    return out


def fetch_moralis_prices():
    if not MORALIS_KEY:
        return []
    url = "https://deep-index.moralis.io/api/v2/erc20/prices"
    data = safe_get(url, headers=HEADERS_MORALIS, label="moralis")
    if not data or "tokens" not in data:
        return []
    out = []
    for t in data["tokens"][:10]:
        sym = t.get("symbol")
        chg = t.get("price_change_24h", "0")
        if sym:
            out.append(_mk(f"{sym} 24h change {chg}%"))
    return out


def fetch_dexscreener():
    url = "https://api.dexscreener.com/latest/dex/tokens/trending"
    data = safe_get(url, label="dexscreener")
    if not isinstance(data, dict):
        return []
    pairs = data.get("pairs") or []
    out = []
    for p in pairs[:10]:
        base = p.get("baseToken", {}) or {}
        sym = base.get("symbol")
        if sym:
            out.append(_mk(f"Dex trending: {sym}"))
    return out


def fetch_coingecko_trending():
    url = "https://api.coingecko.com/api/v3/search/trending"
    data = safe_get(url, label="coingecko")
    if not data or "coins" not in data:
        return []
    out = []
    for c in data["coins"][:10]:
        item = c.get("item", {}) or {}
        sym = item.get("symbol")
        if sym:
            out.append(_mk(f"Trending on CoinGecko: {sym.upper()}"))
    return out


def fetch_pumpfun():
    url = "https://api.pump.fun/api/trending"
    data = safe_get(url, label="pumpfun")
    if not data or "trending" not in data:
        return []
    return [_mk(f"Pump.fun trending: {t.get('symbol','?')}") for t in data["trending"][:10]]


def fetch_etherscan():
    if not ETHERSCAN_KEY:
        return []
    url = "https://api.etherscan.io/api"
    data = safe_get(url, params={
        "module": "account",
        "action": "txlist",
        "address": "0xd8da6bf26964af9d7eed9e03e53415d37aa96045",
        "startblock": 0,
        "endblock": 99999999,
        "sort": "desc",
        "apikey": ETHERSCAN_KEY
    }, label="etherscan")
    if not data or "result" not in data:
        return []
    out = []
    for tx in data["result"][:5]:
        val = tx.get("value")
        out.append(_mk(f"Etherscan activity detected: {val} Wei moved"))
    return out


def fetch_solscan():
    url = "https://api.solscan.io/chaininfo"
    data = safe_get(url, headers=HEADERS_SOLSCAN, label="solscan")
    if not data or "data" not in data:
        return []
    height = data["data"].get("blockHeight")
    txs = data["data"].get("txnCount")
    msg = f"Solana chain: height {height}, {txs} total txs"
    return [_mk(msg)]


def fetch_api_batch():
    all_items = []

    collectors = [
        fetch_marketaux,
        fetch_newsdata,
        fetch_cryptopanic_api,
        fetch_birdeye,
        fetch_moralis_prices,
        fetch_dexscreener,
        fetch_coingecko_trending,
        fetch_pumpfun,
        fetch_etherscan,
        fetch_solscan,
    ]

    for fn in collectors:
        try:
            items = fn()
            print(f"[API] {fn.__name__} → {len(items)}")
            all_items.extend(items)
        except Exception:
            print(f"[API] ERROR in {fn.__name__}")
            traceback.print_exc()

    unique = []
    seen = set()
    for item in all_items:
        h = item["headline"]
        if h not in seen:
            seen.add(h)
            unique.append(item)

    print(f"[API] Total unique → {len(unique)}")
    return unique


if __name__ == "__main__":
    out = fetch_api_batch()
    print(f"[API] Returned → {len(out)}")
