"""
coingecko_cache.py
ToknNews — Free CoinGecko Market Context Cache (1–6)

Provides:
1) price + 24h/7d/30d change
2) market cap rank
3) volume/market cap ratio
4) categories
5) ATH/ATL distance
6) supply metrics

Design:
- Best-effort, never blocks ingestion
- Cached to disk with TTL
- Uses CoinGecko public endpoints
- NO per-story API calls
"""

import json
import time
import requests
from pathlib import Path

# ==============================================================
# PATHS / CONFIG
# ==============================================================

CACHE_DIR = Path("/opt/toknnews/data/cache")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_PATH = CACHE_DIR / "coingecko_market_context.json"
CACHE_TTL_SECONDS = 10 * 60  # 10 minutes

COINGECKO_BASE = "https://api.coingecko.com/api/v3"

# ==============================================================
# CURATED WATCHLIST (SAFE + EXPLICIT)
# ==============================================================

# Core majors + infra
BASE_WATCHLIST = [
    "bitcoin",
    "ethereum",
    "tether",
    "usd-coin",
    "solana",
    "binancecoin",
    "ripple",
    "cardano",
    "dogecoin",
    "tron",
    "avalanche-2",
    "polygon",
    "chainlink",
    "arbitrum",
    "optimism",
]

# Curated trending / frequently surfaced tokens
# (only add tokens you are comfortable attaching prices to)
TRENDING_ALLOWLIST = [
    "zcash",
    "bittensor",
    "ondo-finance",
    "hyperliquid",
    "mon-protocol",
    "pengu",
    "litentry",
    "render-token",
    "fetch-ai",
    "singularitynet",
    "ocean-protocol",
    "pepe",
    "bonk",
    "dogwifcoin",
    "shiba-inu",
]

WATCHLIST = sorted(set(BASE_WATCHLIST + TRENDING_ALLOWLIST))

# ==============================================================
# HELPERS
# ==============================================================

def _safe_get(url: str, params: dict | None = None, timeout: int = 15):
    return requests.get(
        url,
        params=params,
        timeout=timeout,
        headers={"accept": "application/json"},
    )


def load_cache() -> dict:
    if CACHE_PATH.exists():
        try:
            return json.loads(CACHE_PATH.read_text())
        except Exception:
            return {}
    return {}


def cache_is_fresh(cache: dict) -> bool:
    ts = cache.get("_ts", 0)
    return (time.time() - ts) <= CACHE_TTL_SECONDS


# ==============================================================
# CACHE BUILDER
# ==============================================================

def update_cache() -> dict:
    """
    Fetch markets data (1,2,3,5,6) + categories (4) with minimal calls.
    """
    cache: dict = {
        "_ts": time.time(),
        "assets": {},
        "meta": {
            "watchlist_size": len(WATCHLIST),
            "source": "coingecko_public",
        },
    }

    # ----------------------------------------------------------
    # MARKETS SNAPSHOT (covers 1,2,3,5,6)
    # ----------------------------------------------------------
    markets_url = f"{COINGECKO_BASE}/coins/markets"
    params = {
        "vs_currency": "usd",
        "ids": ",".join(WATCHLIST),
        "order": "market_cap_desc",
        "per_page": len(WATCHLIST),
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "24h,7d,30d",
    }

    r = _safe_get(markets_url, params=params)
    if r.status_code != 200:
        # If rate-limited or temporarily unavailable, fall back to existing cache
        return load_cache()

    markets = r.json()

    for row in markets:
        coin_id = row.get("id")
        if not coin_id:
            continue

        price = row.get("current_price")
        mcap = row.get("market_cap")
        vol = row.get("total_volume")

        # 3) volume / market cap ratio
        vol_mcap = None
        try:
            if mcap and vol:
                vol_mcap = float(vol) / float(mcap)
        except Exception:
            pass

        cache["assets"][coin_id] = {
            # 1) price + change
            "price_usd": price,
            "change_24h_pct": row.get("price_change_percentage_24h_in_currency"),
            "change_7d_pct": row.get("price_change_percentage_7d_in_currency"),
            "change_30d_pct": row.get("price_change_percentage_30d_in_currency"),

            # 2) market cap
            "market_cap_rank": row.get("market_cap_rank"),
            "market_cap_usd": mcap,
            "volume_24h_usd": vol,

            # 3) volume/marketcap ratio
            "vol_mcap_ratio": vol_mcap,

            # 5) ATH / ATL
            "ath_usd": row.get("ath"),
            "ath_change_pct": row.get("ath_change_percentage"),
            "atl_usd": row.get("atl"),
            "atl_change_pct": row.get("atl_change_percentage"),

            # 6) supply
            "circulating_supply": row.get("circulating_supply"),
            "total_supply": row.get("total_supply"),
            "max_supply": row.get("max_supply"),
        }

    # ----------------------------------------------------------
    # CATEGORIES (4) — HEAVY, LIMITED TO WATCHLIST
    # ----------------------------------------------------------
    for coin_id in list(cache["assets"].keys()):
        try:
            coin_url = f"{COINGECKO_BASE}/coins/{coin_id}"
            r2 = _safe_get(
                coin_url,
                params={
                    "localization": "false",
                    "tickers": "false",
                    "market_data": "false",
                    "community_data": "false",
                    "developer_data": "false",
                    "sparkline": "false",
                },
                timeout=20,
            )
            if r2.status_code != 200:
                continue
            data = r2.json()
            cache["assets"][coin_id]["categories"] = data.get("categories") or []
        except Exception:
            continue

    CACHE_PATH.write_text(json.dumps(cache, indent=2))
    return cache


# ==============================================================
# PUBLIC API
# ==============================================================

def get_context() -> dict:
    """
    Return fresh cache if possible; update if stale.
    """
    cache = load_cache()
    if cache and cache_is_fresh(cache):
        return cache
    return update_cache()
