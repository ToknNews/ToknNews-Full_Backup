#!/usr/bin/env python3
"""
moralis_enrichment.py
ToknNews — Market Data Enrichment via Moralis

Supports:
- BTC / ETH (EVM)
- SOL
- Extensible to NFTs + more chains

Safe: never crashes service if key is missing.
"""

import os
from typing import Dict
from moralis import evm_api, sol_api


# --------------------------------------------------
# API KEY (lazy + safe)
# --------------------------------------------------

def _get_api_key():
    return os.getenv("MORALIS_API_KEY")


# --------------------------------------------------
# TOKEN PRICE FETCHERS
# --------------------------------------------------

def get_evm_price(symbol: str, address: str) -> Dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Moralis disabled")

    data = evm_api.token.get_token_price(
        api_key=api_key,
        params={
            "address": address,
            "chain": "eth",
            "include": "percent_change"
        }
    )

    return {
        "symbol": symbol,
        "price_usd": float(data.get("usdPrice", 0)),
        "change_24h_pct": float(data.get("usdPrice24hrPercentChange", 0)),
        "volume_24h_usd": float(data.get("usdVolume24hr", 0)),
        "volume_change_pct": float(data.get("usdVolume24hrPercentChange", 0))
    }


def get_sol_price(symbol: str, address: str) -> Dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Moralis disabled")

    data = sol_api.token.get_token_price(
        api_key=api_key,
        params={
            "network": "mainnet",
            "address": address
        }
    )

    return {
        "symbol": symbol,
        "price_usd": float(data.get("usdPrice", 0)),
        "change_24h_pct": float(data.get("usdPrice24hrPercentChange", 0)),
        "volume_24h_usd": float(data.get("usdVolume24hr", 0)),
        "volume_change_pct": float(data.get("usdVolume24hrPercentChange", 0))
    }

# --------------------------------------------------
# TOP ERC-20 MOVERS (MARKET CONTEXT)
# --------------------------------------------------

def get_top_erc20_movers(limit: int = 5) -> Dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Moralis disabled")

    data = evm_api.market.get_top_tokens(
        api_key=api_key,
        params={
            "chain": "eth",
            "limit": limit
        }
    )

    movers = []
    for t in data:
        movers.append({
            "symbol": t.get("symbol"),
            "price_usd": t.get("price_usd"),
            "change_24h_pct": t.get("percent_change_24h")
        })

    return {
        "type": "erc20_movers",
        "tokens": movers
    }

# --------------------------------------------------
# NFT MARKET DATA (TOP SALES)
# --------------------------------------------------

def get_nft_top_sales(collection_address: str, chain: str = "eth") -> Dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Moralis disabled")

    data = evm_api.nft.get_nft_trades(
        api_key=api_key,
        params={
            "address": collection_address,
            "chain": "eth",
            "limit": 5
        }
    )

    sales = data.get("result", [])

    prices = []
    for s in sales:
        if s.get("price"):
            prices.append(float(s["price"]))

    return {
        "top_sales_count": len(prices),
        "top_sale_eth": max(prices) if prices else None,
        "avg_sale_eth": sum(prices) / len(prices) if prices else None
    }

# --------------------------------------------------
# WHALE TRANSFERS (HIGH VALUE MOVES)
# --------------------------------------------------

def get_whale_transfers(token_address: str, min_usd: float = 5_000_000) -> Dict:
    api_key = _get_api_key()
    if not api_key:
        raise RuntimeError("Moralis disabled")

    data = evm_api.token.get_token_transfers(
        api_key=api_key,
        params={
            "address": token_address,
            "chain": "eth",
            "limit": 5
        }
    )

    whales = []
    for tx in data.get("result", []):
        usd_value = float(tx.get("value_usd", 0))
        if usd_value >= min_usd:
            whales.append({
                "from": tx.get("from_address"),
                "to": tx.get("to_address"),
                "usd_value": usd_value
            })

    return {
        "type": "whale_transfers",
        "count": len(whales),
        "transfers": whales
    }


# --------------------------------------------------
# PUBLIC API — SAFE ENRICHER
# --------------------------------------------------

def enrich_story(story: Dict) -> Dict:
    """
    Attaches market_data to a story dict.
    Never crashes pipeline.
    """

    api_key = _get_api_key()
    if not api_key:
        story["market_data_status"] = "moralis_disabled"
        return story

    story.setdefault("market_data", {})

    symbol  = story.get("symbol")
    chain   = story.get("chain")
    address = story.get("address")

    try:
        # -----------------------------
        # PRICE ENRICHMENT
        # -----------------------------
        if symbol and chain and address:
            if chain == "eth":
                story["market_data"]["price"] = get_evm_price(symbol, address)
            elif chain == "sol":
                story["market_data"]["price"] = get_sol_price(symbol, address)

        # -----------------------------
        # MARKET CONTEXT (global)
        # -----------------------------
        if story.get("domain") == "markets":
            story["market_data"]["erc20_movers"] = get_top_erc20_movers()

        # -----------------------------
        # NFT SALES
        # -----------------------------
        if story.get("domain") == "nft" and story.get("collection_address"):
            story["market_data"]["nft_sales"] = get_nft_top_sales(
                story["collection_address"]
            )

        # -----------------------------
        # WHALE MOVES
        # -----------------------------
        if symbol and address and chain == "eth":
            story["market_data"]["whales"] = get_whale_transfers(address)

    except Exception as e:
        story["market_data_error"] = str(e)

    return story


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":
    test_stories = [
        {
            "symbol": "ETH",
            "chain": "eth",
            "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        },
        {
            "symbol": "SOL",
            "chain": "sol",
            "address": "So11111111111111111111111111111111111111112"
        }
    ]

    for s in test_stories:
        print(enrich_story(s))
