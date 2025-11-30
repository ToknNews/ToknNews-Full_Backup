#!/usr/bin/env python3
"""
ToknNews Pump.fun Ingestor
Pulls trending meme coins from Pump.fun API.
"""

import requests, json, time
from datetime import datetime
from update_heartbeat import update_field

URL = "https://api.pump.fun/api/trending"
OUTFILE = "/var/www/toknnews/data/raw/pumpfun_latest.json"
HEADERS = {"User-Agent": "ToknNewsBot/1.0"}

def fetch_pumpfun():
    start = time.time()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        latency = int((time.time() - start) * 1000)
        update_field("pumpfun_latency_ms", latency)

        if not r.ok:
            update_field("pumpfun", "fail")
            print(f"[Pump.fun] ❌ HTTP error {r.status_code}")
            return

        data = r.json()
        coins = data.get("tokens") or data  # handle possible structure variants
        if not coins:
            update_field("pumpfun", "empty")
            print("[Pump.fun] ⚠️ No tokens returned.")
            return

        parsed = []
        for c in coins[:50]:  # limit to 50 top tokens
            parsed.append({
                "symbol": c.get("symbol") or c.get("ticker") or "?",
                "name": c.get("name") or "Unknown",
                "price": c.get("priceUsd") or c.get("price") or "0",
                "marketCap": c.get("marketCap") or c.get("fdv") or 0,
                "volume_24h": c.get("volume24h") or c.get("volume") or 0,
                "chain": c.get("chain") or "sol",
                "url": f"https://pump.fun/{c.get('symbol','')}",
                "timestamp": datetime.utcnow().isoformat()
            })

        with open(OUTFILE, "w") as f:
            json.dump(parsed, f, indent=2)

        update_field("pumpfun", "ok")
        print(f"[Pump.fun] ✅ Wrote {len(parsed)} tokens → {OUTFILE}")

    except Exception as e:
        update_field("pumpfun", "fail")
        print("[Pump.fun] ❌ Error:", e)

if __name__ == "__main__":
    fetch_pumpfun()
