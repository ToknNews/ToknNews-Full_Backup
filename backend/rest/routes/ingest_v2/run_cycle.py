#!/usr/bin/env python3
import os, requests, time, json
from loguru import logger

# YOUR KEYS
MORALIS_KEY = os.getenv("MORALIS_API_KEY")
BIRDEYE_KEY = os.getenv("BIRDEYE_API_KEY")
CRYPTOPANIC_KEY = os.getenv("CRYPTOPANIC_API_KEY")

def safe_get(url, headers=None):
    try:
        r = requests.get(url, headers=headers or {}, timeout=15)
        return r.json() if r.status_code == 200 else None
    except:
        return None

while True:
    stories = []

    # Moralis — your key
    if MORALIS_KEY:
        data = safe_get("https://deep-index.moralis.io/api/v2/erc20/top-tokens?chain=eth", headers={"X-API-Key": MORALIS_KEY})
        if data and "result" in data:
            for t in data["result"][:10]:
                vol = t.get("volume_24h", "0")
                try:
                    vol_num = int(float(vol))
                    vol_str = f"${vol_num:,.0f}"
                except:
                    vol_str = vol
                stories.append({"headline": f"{t['symbol']} {vol_str} 24h vol (on-chain)"})

    # Birdeye — your key
    if BIRDEYE_KEY:
        data = safe_get("https://public-api.birdeye.so/defi/tokenlist?sort_by=v24hUSD&sort_type=desc&limit=10", headers={"x-api-key": BIRDEYE_KEY})
        if data and "data" in data:
            for t in data["data"][:8]:
                stories.append({"headline": f"SOLANA: {t['symbol']} ${t.get('v24hUSD',0):,.0f} vol"})

    # CryptoPanic — your key
    if CRYPTOPANIC_KEY:
        data = safe_get(f"https://cryptopanic.com/api/v1/posts/?auth_token={CRYPTOPANIC_KEY}&public=true&filter=hot")
        if data and "results" in data:
            for p in data["results"][:8]:
                stories.append({"headline": p["title"]})

    # WRITE TO THE FILE THE SHOW ACTUALLY READS
    path = "/var/www/toknnews-live/data/rolling_stories.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(stories[:18], f, indent=2)
    
    logger.info(f"WRITING TO ROLLING_STORIES.JSON — {len(stories)} headlines")
    time.sleep(180)
