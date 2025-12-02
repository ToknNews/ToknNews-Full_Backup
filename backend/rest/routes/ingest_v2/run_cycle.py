#!/usr/bin/env python3

import sys
sys.path.append("/opt/toknnews/backend/runtime")
from vault_loader import load_secrets

import os, requests, time, json, feedparser, re
from loguru import logger

from rest.sources.crypto_rss import get_crypto_rss

# ============================================
# LOAD SECRETS
# ============================================
SECRETS = load_secrets()

MARKETAUX_KEY = SECRETS.get("marketaux_api_key", "")
BIRDEYE_KEY   = SECRETS.get("birdeye_api_key", "")
MORALIS_KEY   = SECRETS.get("moralis_api_key", "")

# ============================================
# DEBUG LOGGER
# ============================================
def debug_api(name, data):
    if data is None:
        logger.warning(f"[{name}] returned None")
    elif isinstance(data, dict):
        logger.info(f"[{name}] keys: {list(data.keys())}")
    elif isinstance(data, list):
        logger.info(f"[{name}] list[{len(data)}]")
    else:
        logger.warning(f"[{name}] non-JSON {str(data)[:120]}")

# ============================================
# SAFE JSON GET
# ============================================
def safe_get(url, headers=None):
    try:
        r = requests.get(url, headers=headers or {}, timeout=15)
        try:
            return r.json()
        except:
            return None
    except:
        return None

# ============================================
# RSS FEEDS (GLOBAL NEWS)
# ============================================
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://www.theblock.co/rss.xml",
    "https://decrypt.co/feed"
]

def get_global_rss():
    stories = []
    boring = re.compile(r"(how|what is|guide|top \\d+)", re.I)
    for feed in RSS_FEEDS:
        try:
            f = feedparser.parse(feed)
            for e in f.entries[:10]:
                if boring.search(e.title):
                    continue
                stories.append({
                    "headline": e.title,
                    "source": "RSS"
                })
        except:
            pass
    return stories

# ============================================
# MORALIS — CONTRACT PRICE ENDPOINTS
# ============================================
MORALIS_CONTRACTS = [
    ("WETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    ("USDT", "0xdAC17F958D2ee523a2206206994597C13D831ec7"),
    ("LINK", "0x514910771AF9Ca656af840dff83E8264EcF986CA"),
    ("WBTC", "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
    ("UNI",  "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"),
]

# ============================================
# MAIN INGEST LOOP
# ============================================
while True:

    stories = []

    # ---------------------------------------------
    # MARKET AUX
    # ---------------------------------------------
    if MARKETAUX_KEY:
        data = safe_get(
            f"https://api.marketaux.com/v1/news/all?crypto=1&filter_entities=true&language=en&api_token={MARKETAUX_KEY}"
        )
        debug_api("Marketaux", data)

        if data and "data" in data:
            for item in data["data"][:8]:
                stories.append({
                    "headline": item["title"],
                    "source": "Marketaux"
                })

    # ---------------------------------------------
    # BIRDEYE (OPTIONAL)
    # ---------------------------------------------
    if BIRDEYE_KEY:
        data = safe_get(
            "https://public-api.birdeye.so/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&limit=10",
            {"x-api-key": BIRDEYE_KEY}
        )
        debug_api("Birdeye", data)

        if data and "data" in data:
            for t in data["data"][:6]:
                stories.append({
                    "headline": f"SOLANA: {t['symbol']} ${t.get('v24hUSD',0):,.0f} vol",
                    "source": "Birdeye"
                })

    # ---------------------------------------------
    # EXTENDED CRYPTOPANIC RSS (NO TOKEN REQUIRED)
    # ---------------------------------------------
    try:
        stories.extend(get_crypto_rss())
    except Exception as e:
        logger.warning(f"[CryptoPanic-Extended] failed: {e}")

    # ---------------------------------------------
    # MORALIS (CONTRACT PRICES)
    # ---------------------------------------------
    if MORALIS_KEY:
        for symbol, address in MORALIS_CONTRACTS:
            data = safe_get(
                f"https://deep-index.moralis.io/api/v2/erc20/{address}/price?chain=eth",
                {"X-API-Key": MORALIS_KEY}
            )
            debug_api(f"Moralis-{symbol}", data)

            if data and isinstance(data, dict) and "usdPrice" in data:
                price = data["usdPrice"]
                stories.append({
                    "headline": f"{symbol}: ${price:,.2f} (Moralis)",
                    "source": "Moralis"
                })

    # ---------------------------------------------
    # GLOBAL RSS
    # ---------------------------------------------
    stories.extend(get_global_rss())

    # ---------------------------------------------
    # DEDUPE
    # ---------------------------------------------
    seen = set()
    unique = []
    for s in stories:
        if s["headline"] not in seen:
            seen.add(s["headline"])
            unique.append(s)

    # ---------------------------------------------
    # WRITE RESULTS
    # ---------------------------------------------
    path = "/var/www/toknnews-live/data/rolling_stories.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(unique[:18], f, indent=2)

    logger.info(f"INGEST COMPLETED — {len(unique)} headlines")

    time.sleep(180)
