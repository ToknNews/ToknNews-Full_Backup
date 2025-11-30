#!/usr/bin/env python3
"""
ToknNews DexScreener Ingestor
Fetches latest trending pairs and writes summary JSON for scene compiler.
"""

import requests, json, time
from datetime import datetime
from update_heartbeat import update_field

URL = "https://api.dexscreener.com/latest/dex/search/?q=SOL"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; ToknNewsBot/1.0; +https://toknnews.com)"}
OUTFILE = "/var/www/toknnews/data/raw/api_latest.json"

def fetch_dexscreener():
    start = time.time()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=15)
        latency = int((time.time() - start) * 1000)
        update_field("dexscreener_latency_ms", latency)

        if not r.ok:
            update_field("dexscreener", "fail")
            print("[DexScreener] ❌ HTTP error", r.status_code)
            return

        data = r.json().get("pairs", [])
        if not data:
            update_field("dexscreener", "empty")
            print("[DexScreener] ⚠️ No data returned")
            return

        parsed = []
        for p in data[:100]:
            parsed.append({
                "symbol": p["baseToken"]["symbol"],
                "name": p["baseToken"].get("name", ""),
                "price": p.get("priceUsd", "0"),
                "chain": p.get("chainId", ""),
                "dex": p.get("dexId", ""),
                "url": p.get("url", ""),
                "buys_5m": p["txns"]["m5"].get("buys", 0),
                "sells_5m": p["txns"]["m5"].get("sells", 0),
                "timestamp": datetime.utcnow().isoformat()
            })

        with open(OUTFILE, "w") as f:
            json.dump(parsed, f, indent=2)

        update_field("dexscreener", "ok")
        print(f"[DexScreener] ✅ Wrote {len(parsed)} pairs → {OUTFILE}")

    except Exception as e:
        update_field("dexscreener", "fail")
        print("[DexScreener] ❌ Error:", e)

if __name__ == "__main__":
    fetch_dexscreener()
    import filter_dexscreener
    filter_dexscreener.filter_signals()
