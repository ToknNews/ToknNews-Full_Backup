#!/usr/bin/env python3
"""
ToknNews Moralis API Ingestor (Free Plan – Solana Tokens)
Pulls token prices & basic stats for selected Solana tokens
and computes a simple "signal score" for scene generation.
"""

import requests, json, time
from datetime import datetime
from update_heartbeat import update_field

API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6IjBjODQ3ZGMyLWYxMjUtNDQyNi05NDg1LTYwNDc3ZWQ3NDM0ZiIsIm9yZ0lkIjoiNDc5NTA4IiwidXNlcklkIjoiNDkzMzE1IiwidHlwZUlkIjoiYTEwNGI0MjQtOWRlNy00NTliLTg2NjItNTQ2ZWNiM2ZiMjIzIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3NjIyNzY2MzksImV4cCI6NDkxODAzNjYzOX0.zyyEkqf9WmxXlrR84s1iWRcSXf_z-WJ3gHuG95_Ufn8"  # <-- keep quotes
OUTFILE = "/var/www/toknnews/data/raw/moralis_latest.json"

# Define key Solana meme / ecosystem tokens (expand as needed)
TOKENS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "BONK": "DezXAZ8z7PnrnRJjz3wXboTcDC8g9RQtVb5uAjKQZbQj",
    "JUP": "JUPy4vQFGDX7Q8Qvu7Q15qALRkUS8WxiU8KDPisgAp7",
    "WIF": "DmbL1Nbgp1iAfApR8oMio8XDyzh4WmctZKdPdrgAFzQz",
    "SAMO": "7xKXtg2CW87d97TXJSDpbD5eYBzGq7fi5qfA9jS88oJe"
}

HEADERS = {
    "X-API-Key": API_KEY.strip(),
    "Accept": "application/json",
    "User-Agent": "ToknNewsBot/1.0"
}

def fetch_token_price(address: str):
    """Fetch USD price + change % for a given Solana token."""
    url = f"https://solana-gateway.moralis.io/token/mainnet/{address}/price"
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.ok:
        data = r.json()
        return data.get("usdPrice", 0), data.get("percentChange24h", 0)
    return None, None


def fetch_holders(address: str):
    """Optional: fetch token holders count (free endpoint)."""
    url = f"https://solana-gateway.moralis.io/token/mainnet/{address}/holders"
    r = requests.get(url, headers=HEADERS, timeout=10)
    if r.ok:
        data = r.json()
        return len(data.get("result", []))
    return 0


def fetch_moralis():
    start = time.time()
    results = []
    try:
        for symbol, address in TOKENS.items():
            price, change = fetch_token_price(address)
            holders = fetch_holders(address)
            if price is None:
                print(f"[Moralis] ⚠️ {symbol} unavailable.")
                continue

            # Simple signal score: price change + holder trend proxy
            signal = round(min(100, abs(change) + (holders / 1000)), 2)

            results.append({
                "symbol": symbol,
                "price": round(price, 8),
                "percent_change_24h": change,
                "holders": holders,
                "signal_score": signal,
                "chain": "sol",
                "source": "Moralis",
                "timestamp": datetime.utcnow().isoformat(),
                "url": f"https://moralis.io/token/{address}"
            })
            time.sleep(0.5)  # avoid rate limits

        # Save JSON
        with open(OUTFILE, "w") as f:
            json.dump(results, f, indent=2)

        latency = int((time.time() - start) * 1000)
        update_field("moralis_latency_ms", latency)
        update_field("moralis", "ok")
        print(f"[Moralis] ✅ Wrote {len(results)} tokens → {OUTFILE}")

    except Exception as e:
        update_field("moralis", "fail")
        print("[Moralis] ❌ Error:", e)


if __name__ == "__main__":
    fetch_moralis()
