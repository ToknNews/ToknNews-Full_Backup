#!/usr/bin/env python3
# /opt/toknnews/backend/live/toknnews_market_intel.py

import os
import json
import requests
from datetime import datetime
from pathlib import Path

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
if not MORALIS_API_KEY:
    raise RuntimeError("Missing MORALIS_API_KEY environment variable")
HEADERS = {"X-API-Key": MORALIS_API_KEY}

CONFIG_FILE = Path("/opt/toknnews/config/contracts.json")

def load_contracts():
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def get_token_price(chain, address):
    url = f"https://deep-index.moralis.io/api/v2.2/erc20/{address}/price"
    params = {"chain": chain}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        return {"error": f"token {address} on {chain} failed", "status": r.status_code}
    except Exception as e:
        return {"error": str(e)}

def get_nft_floor_price(chain, address):
    url = f"https://deep-index.moralis.io/api/v2.2/nft/{address}/price"
    params = {"chain": chain}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=10)
        if r.status_code == 200:
            return r.json()
        return {"error": f"nft {address} on {chain} failed", "status": r.status_code}
    except Exception as e:
        return {"error": str(e)}

def collect_market_signals():
    results = []
    contracts = load_contracts()

    for chain, categories in contracts.items():
        for token_addr in categories.get("erc20", []):
            data = get_token_price(chain, token_addr)
            results.append({
                "type": "token_price",
                "chain": chain,
                "address": token_addr,
                "data": data
            })
        for nft_type in ("nft721", "nft1155"):
            for nft_addr in categories.get(nft_type, []):
                data = get_nft_floor_price(chain, nft_addr)
                results.append({
                    "type": "nft_floor",
                    "chain": chain,
                    "contract_type": nft_type,
                    "address": nft_addr,
                    "data": data
                })
    return results

if __name__ == "__main__":
    signals = collect_market_signals()
    outfile = f"/opt/toknnews/data/sources/market_intel_{datetime.now().strftime('%Y%m%d')}.json"
    with open(outfile, "w") as f:
        json.dump(signals, f, indent=2)
    print(f"[MarketIntel] ✅ Collected {len(signals)} signals → {outfile}")
