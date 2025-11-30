#!/usr/bin/env python3
"""
domain_rebalance.py
TOKEN NEWS — Strong Crypto Boost Domain Engine (Phase 3B)

Rebalances domains to ensure ToknNews skews crypto-first.
"""

import re

CRYPTO_MAP = {
    "bitcoin": "bitcoin",
    "btc": "bitcoin",
    "ethereum": "ethereum",
    "eth": "ethereum",
    "altcoin": "altcoins",
    "altcoins": "altcoins",
    "layer-2": "crypto",
    "l2": "crypto",
    "stablecoin": "stablecoins",
    "usdt": "stablecoins",
    "usdc": "stablecoins",
    "defi": "defi",
    "dex": "defi",
    "liquid staking": "defi",
    "staking": "defi",
    "restaking": "defi",
    "yield": "defi",
    "onchain": "onchain",
    "on-chain": "onchain",
    "whale": "onchain",
    "wallet": "onchain",
    "nft": "nfts",
    "nfts": "nfts",
    "web3": "nfts",
    "metaverse": "nfts",
    "token": "crypto",
    "tokenization": "crypto",
    "tokenized": "crypto",
}

ASIA_MACRO_SUPPRESS = [
    "PSEi", "Philippine", "BSP", "peso", "Bangko Sentral",
    "Manila", "Indonesia", "Vietnam", "Thailand", "Malaysia",
    "China", "Taiwan", "Korea", "GDP", "inflation", "exports"
]

def rebalance_domain(headline: str, summary: str, original_domain: str):

    text = f"{headline} {summary}".lower()

    # 1. Hard crypto detection first
    for key, dom in CRYPTO_MAP.items():
        if key in text:
            return dom

    # 2. Suppress Asia/PSEi macro dominance
    for term in ASIA_MACRO_SUPPRESS:
        if term.lower() in text:
            return "macro_suppressed"

    # 3. Downweight non-crypto markets
    if original_domain in ["markets", "macro"]:
        return "markets_low"

    # 4. Fallback
    return original_domain
