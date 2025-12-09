#!/usr/bin/env python3
"""
domain_classifier.py — ToknNews Editorial Engine v4

Classify a story into an editorial domain using simple, fast rules.
More complex persona routing still lives in your PD / context_router.
"""

from typing import Dict

DOMAIN_KEYWORDS = {
    "markets": [
        "price", "etf", "spot etf", "futures", "market", "trading",
        "volume", "rally", "selloff", "dump", "pump"
    ],
    "defi": [
        "defi", "tvl", "staking", "yield", "uniswap", "curve",
        "lending", "amm", "liquidity pool"
    ],
    "ai": [
        "ai", "gpu", "model", "training", "inference", "compute",
        "nvidia", "openai", "anthropic"
    ],
    "regulation": [
        "sec", "cftc", "law", "regulation", "policy", "ban",
        "lawsuit", "compliance", "hearing", "congress"
    ],
    "onchain": [
        "on-chain", "onchain", "wallet", "whale", "address",
        "transaction", "gas", "hashrate", "miner"
    ],
    "sentiment": [
        "fear", "greed", "sentiment", "euphoria", "panic",
        "fomo", "fud", "confidence"
    ],
    "culture": [
        "meme", "community", "twitter", "ct", "viral", "trend",
        "nft", "pfp", "culture"
    ],
    "macro": [
        "fed", "inflation", "rates", "treasury", "bond yields",
        "jobs report", "recession", "macro"
    ],
    "risk": [
        "hack", "exploit", "breach", "vulnerability", "downtime",
        "risk", "liquidation cascade"
    ],
}


def classify_domain(story: Dict) -> str:
    """
    Takes a normalized story dict:
        { "headline": ..., "body": ..., ... }
    Returns a domain label: markets/defi/ai/regulation/onchain/etc.
    """

    text = f"{story.get('headline','')} {story.get('body','')}".lower()

    scores = {d: 0 for d in DOMAIN_KEYWORDS}

    for domain, words in DOMAIN_KEYWORDS.items():
        for w in words:
            if w in text:
                scores[domain] += 1

    # pick the best domain
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "general"

    return best


if __name__ == "__main__":
    sample = {
        "headline": "Ethereum liquidations surge as markets turn risk-off",
        "body": "Traders watch on-chain flows as gas prices spike."
    }
    print(classify_domain(sample))
