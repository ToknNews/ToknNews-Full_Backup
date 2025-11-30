#!/usr/bin/env python3
import os, requests, time, json, feedparser, re, random
from loguru import logger
from datetime import datetime

# Your keys (from .env)
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_API_KEY")
MARKETAUX_KEY = os.getenv("MARKETAUX_API_KEY")
NEWDATA_KEY = os.getenv("NEWDATA_API_KEY")
MORALIS_KEY = os.getenv("MORALIS_API_KEY")
DUNE_KEY = os.getenv("DUNE_API_KEY")
NANSEN_KEY = os.getenv("NANSEN_API_KEY")
BIRDEYE_KEY = os.getenv("BIRDEYE_API_KEY")
ETHERSCAN_KEY = os.getenv("ETHERSCAN_API_KEY")

# RSS feeds (filtered)
RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://www.theblock.co/rss.xml"
]

# Filler filter (kills explainers)
BORING_PATTERNS = re.compile(r"(?i)(how|what is|guide|beginner|vs|compare|top \d+|understanding|from idea to)", re.IGNORECASE)

def safe_get(url, headers=None, timeout=15):
    try:
        r = requests.get(url, headers=headers or {}, timeout=timeout)
        if r.status_code == 429:
            time.sleep(random.uniform(5, 15))
            return safe_get(url, headers, timeout)
        if r.status_code != 200:
            return None
        return r.json() if "application/json" in r.headers.get("content-type", "") else r.text
    except:
        return None

def get_x_sentiment(headline):
    # Use X tools for live sentiment
    # (This is a placeholder — we'll call the tool in production)
    return "HOTTEST X TAKES: Cobie: 'This is DeFi summer 2.0' (12K likes). Ansem: 'Rug incoming' (8K retweets)."

def get_rss_stories():
    stories = []
    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries[:12]:
                title = entry.title
                if BORING_PATTERNS.search(title):
                    continue
                if any(kw in title.lower() for kw in ["sec","etf","pump","rug","whale","tether","binance","solana","berachain"]):
                    stories.append({
                        "headline": title,
                        "url": entry.link,
                        "source": "RSS"
                    })
        except Exception as e:
            logger.error(f"RSS failed {feed_url}: {e}")
    return stories

def get_api_stories():
    stories = []

    # DexScreener trending
    data = safe_get("https://api.dexscreener.com/latest/dex/tokens/trending")
    if data:
        for item in data[:10]:
            sym = item["pair"]["baseToken"]["symbol"]
            change = item["priceChange"]["h24"]
            vol = item.get("volume", {}).get("h24", 0)
            headline = f"{sym} {change:+.1f}% — ${vol:,.0f} vol"
            stories.append({"headline": headline, "source": "DexScreener"})

    # Pump.fun launches
    data = safe_get("https://frontend-api.pump.fun/coins?limit=15&sort=created_timestamp&order=desc")
    if data:
        for item in data[:6]:
            age = int(time.time() - item["created_timestamp"])
            headline = f"PUMP.FUN: {item['symbol']} launched {age//60}m ago"
            stories.append({"headline": headline, "source": "Pump.fun"})

    # Birdeye Solana volume
    if BIRDEYE_KEY:
        headers = {"x-api-key": BIRDEYE_KEY}
        data = safe_get("https://public-api.birdeye.so/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&limit=10", headers)
        if data:
            for item in data.get("data", [])[:6]:
                headline = f"SOLANA: {item['symbol']} ${item.get('v24hUSD',0):,.0f} vol"
                stories.append({"headline": headline, "source": "Birdeye"})

    # CryptoPanic (your key)
    if CRYPTOPANIC_KEY:
        data = safe_get(f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&public=true&filter=hot")
        if data:
            for item in data.get("results", [])[:8]:
                headline = item["title"]
                if not BORING_PATTERNS.search(headline):
                    stories.append({"headline": headline, "source": "CryptoPanic"})

    # Dedupe
    seen = set()
    unique = [s for s in stories if s["headline"] not in seen and not seen.add(s["headline"])]

    return unique

def fetch_all():
    api_stories = get_api_stories()
    rss_stories = get_rss_stories()
    stories = api_stories + rss_stories
    return stories[:18]

while True:
    try:
        stories = fetch_all()
        path = "/opt/toknnews/data/stories/latest.json"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as f:
            json.dump(stories, f, indent=2)
        logger.info(f"COMPLETE INGEST: {len(stories)} headlines — APIs + RSS")
    except Exception as e:
        logger.error(f"Crash: {e}")
    time.sleep(180)
