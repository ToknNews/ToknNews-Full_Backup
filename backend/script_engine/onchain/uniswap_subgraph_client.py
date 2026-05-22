#!/usr/bin/env python3
"""
uniswap_subgraph_client.py

ToknNews — Uniswap V3 Subgraph Client

PURPOSE:
- Fetch aggregated DEX context (volume, TVL, tx count)
- Used for narrative + signals context
- NOT a price authority

SOURCE:
- The Graph public Uniswap V3 subgraphs
"""

import requests
from typing import Dict, Any

# ---------------------------------------------------------
# SUBGRAPH ENDPOINTS (LOCKED)
# ---------------------------------------------------------

UNISWAP_SUBGRAPHS = {
    "ethereum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3",
    "base": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-base",
    "arbitrum": "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3-arbitrum",
}

# ETH/USDC canonical pool IDs (lowercase!)
UNISWAP_POOL_IDS = {
    "ethereum": "0x88e6a0c2ddd26feeb64f039a2c41296fcb3f5640",
    "base": "0x4c36388be6f416a29c8d8eee81c771ce6be14b18",
    "arbitrum": "0xc6962004f452be9203591991d15f6b388e09e8d0",
}

# ---------------------------------------------------------
# CORE QUERY
# ---------------------------------------------------------

POOL_QUERY = """
query pool($id: ID!) {
  pool(id: $id) {
    volumeUSD
    liquidity
    txCount
  }
}
"""

# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

def fetch_uniswap_liquidity(chain: str) -> Dict[str, Any] | None:
    """
    Fetch aggregated liquidity + volume metrics for a chain.
    """

    endpoint = UNISWAP_SUBGRAPHS.get(chain)
    pool_id = UNISWAP_POOL_IDS.get(chain)

    if not endpoint or not pool_id:
        return None

    try:
        resp = requests.post(
            endpoint,
            json={
                "query": POOL_QUERY,
                "variables": {"id": pool_id},
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()["data"]["pool"]

        return {
            "dex_volume_24h_usd": float(data["volumeUSD"]),
            "tvl_raw": float(data["liquidity"]),
            "tx_count_total": int(data["txCount"]),
            "source": "uniswap_subgraph",
        }

    except Exception as e:
        print(f"[SUBGRAPH][WARN] {chain} fetch failed: {e}")
        return None
