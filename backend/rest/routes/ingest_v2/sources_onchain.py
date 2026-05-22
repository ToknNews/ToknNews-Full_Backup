"""
sources_onchain.py
ToknNews — Moralis On-Chain Ingestion (RAW EVENTS ONLY)

Purpose:
- Pull HIGH-SIGNAL on-chain events
- Minimal CU usage
- No polling
- No price loops
- No editorial logic
"""

import os
import time
import requests

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")

BASE_URL = "https://deep-index.moralis.io/api/v2"

HEADERS = {
    "X-API-Key": MORALIS_API_KEY,
    "Accept": "application/json"
}

# -----------------------------
# HARD LIMITS (COST CONTROL)
# -----------------------------
MAX_EVENTS = 5
MIN_USD_THRESHOLD = 1_000_000  # $1M+

# -----------------------------
# TARGET CHAINS / TOKENS
# -----------------------------
WATCH_CHAINS = ["eth"]
STABLECOINS = ["USDT", "USDC"]

def fetch_large_transfers():
    """
    Fetch large stablecoin transfers using Moralis indexed endpoints.
    This is cheap and high signal.
    """
    events = []

    if not MORALIS_API_KEY:
        print("[INGEST][ONCHAIN] Moralis API key missing")
        return events

    for chain in WATCH_CHAINS:
        for token in STABLECOINS:
            try:
                url = f"{BASE_URL}/erc20/{token}/transfers"
                params = {
                    "chain": chain,
                    "limit": MAX_EVENTS
                }

                r = requests.get(url, headers=HEADERS, params=params, timeout=15)
                if r.status_code != 200:
                    continue

                data = r.json().get("result", [])
                for tx in data:
                    usd = float(tx.get("value_usd", 0) or 0)
                    if usd < MIN_USD_THRESHOLD:
                        continue

                    events.append({
                        "headline": f"Large {token} transfer on {chain.upper()}",
                        "summary": (
                            f"An on-chain transfer of approximately ${usd:,.0f} "
                            f"in {token} was recorded on {chain.upper()}."
                        ),
                        "domain": "onchain",
                        "source": "moralis",
                        "timestamp": time.time(),
                        "semantic_keys": {
                            "domain": "onchain",
                            "assets": [token],
                            "event_type": "large_transfer",
                            "confidence": 0.9
                        }
                    })

            except Exception as e:
                print("[INGEST][ONCHAIN] Error:", e)

    return events


def fetch_onchain_batch():
    """
    Public entry point for ingest_controller.
    Returns list of raw Story Lake items.
    """
    events = []
    events.extend(fetch_large_transfers())
    return events
