#!/usr/bin/env python3
"""
context_router.py
TOKEN NEWS — AI-Enhanced Domain & Persona Routing

This version replaces static PRIMARY_ANCHOR logic with a weighted vector
matching system to intelligently route any headline to the correct anchor.

Inspired by newsroom role logic + semantic scoring.
"""

import re
from collections import defaultdict

# ================================================================
# 1. DOMAIN VECTOR MAP — Defines the thematic clusters for routing
# ================================================================
DOMAIN_VECTORS = {

    "defi": [
        "defi", "yield", "liquidity", "staking", "tvl", "amm",
        "bridge", "protocol", "dapp", "tokenomics", "vault"
    ],

    "ai": [
        "ai", "artificial intelligence", "gpu", "compute", "chip",
        "model", "training", "inference", "llm", "neural", "hardware"
    ],

    "macro": [
        "inflation", "interest rate", "jobs", "gdp", "economy", "fed",
        "ecb", "macro", "unemployment", "liquidity crisis", "recession"
    ],

    "regulation": [
        "sec", "regulation", "lawsuit", "legal", "cftc", "policy",
        "compliance", "bill", "legislation", "court"
    ],

    "markets": [
        "stock", "market cap", "price target", "s&p", "nasdaq",
        "equities", "trading", "volume", "volatility"
    ],

    "onchain": [
        "wallet", "token transfer", "contract", "on-chain", "block",
        "cluster activity", "gas fee", "hashrate", "miner"
    ],

    "retail": [
        "consumer", "everyday users", "lifestyle", "spending", "adoption",
        "habits", "mass-market"
    ],

    "sentiment": [
        "fear", "euphoria", "sentiment", "emotion", "conviction",
        "crowd psychology", "behavior"
    ],

    "venture": [
        "funding", "valuation", "runway", "investor", "term sheet",
        "capital", "founder", "series a", "venture"
    ],

    "trader": [
        "fomo", "bagholder", "momentum", "exit liquidity", "liquidation",
        "leverage", "pump", "dump"
    ],

    "volatility": [
        "liquidation", "volatility spike", "margin call", "flash crash",
        "chaos", "late night"
    ],

    "meta": [
        "meme", "social", "crypto twitter", "reaction", "community meltdown",
        "timeline", "trend"
    ]
}


# ================================================================
# 2. PERSONA → DOMAIN WEIGHTS
# Higher weight = persona is stronger in that domain
# ================================================================
PERSONA_WEIGHTS = {

    "chip":     {"macro": 0.6, "markets": 0.7, "general": 1.0},
    "reef":     {"defi": 1.0, "onchain": 0.6, "markets": 0.3},
    "neura":    {"ai": 1.0, "tech": 0.6, "macro": 0.2},
    "ledger":   {"onchain": 1.0, "defi": 0.3, "security": 0.5},
    "lawson":   {"regulation": 1.0, "compliance": 0.7},
    "cap":      {"venture": 1.0, "markets": 0.4},
    "bond":     {"macro": 1.0, "markets": 0.6, "global": 0.6},
    "ivy":      {"sentiment": 1.0, "retail": 0.6},
    "cash":     {"trader": 1.0, "sentiment": 0.5},
    "penny":    {"retail": 1.0, "sentiment": 0.4},
    "rex":      {"volatility": 1.0, "markets": 0.5},
    "bitsy":    {"meta": 1.0},
    "vega":     {"identity": 1.0}
}


# ================================================================
# 3. Tokenization / keyword extraction
# ================================================================
def tokenize(text: str):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s\-]", " ", text)
    return text.split()


# ================================================================
# 4. Score headline against domains using vector weights
# ================================================================
def score_domains(tokens):
    scores = defaultdict(float)

    for token in tokens:
        for domain, keywords in DOMAIN_VECTORS.items():
            if token in keywords:
                scores[domain] += 1.0   # base score

    return scores


# ================================================================
# 5. Score personas using weighted domain scores
# ================================================================
def score_personas(domain_scores):
    persona_scores = defaultdict(float)

    for persona, weights in PERSONA_WEIGHTS.items():
        for domain, weight in weights.items():
            persona_scores[persona] += domain_scores.get(domain, 0.0) * weight

    return persona_scores


# ================================================================
# 6. Public API — pick best persona for headline
# ================================================================
def route_persona_for_headline(headline: str) -> str:
    tokens = tokenize(headline)
    domain_scores = score_domains(tokens)
    persona_scores = score_personas(domain_scores)

    if not persona_scores:
        return "chip"

    return max(persona_scores, key=persona_scores.get)


# ================================================================
# 7. Legacy compatibility shim
# ================================================================
def get_context_for_anchor(anchor: str) -> dict:
    """
    Provide a simple context object for GPT and PD.
    Compatible with existing script_engine code.
    """

    anchor = anchor.lower().strip()

    return {
        "anchor": anchor,
        "persona_class": PERSONA_WEIGHTS.get(anchor, {}),
        "notes": f"Use {anchor}'s GPT seed + persona config.",
        "pd_flags": {
            "is_breaking": False,
            "volatility_risk": 0.0,
            "social_heat": 0.0
        }
    }


# ================================================================
# 8. Test mode
# ================================================================
if __name__ == "__main__":
    tests = [
        "SEC investigates major crypto exchange",
        "Ethereum staking incentives surge as TVL climbs",
        "AI chips boost Nvidia market cap",
        "Mass liquidation wipes out overleveraged traders",
        "Funding round extends startup runway",
        "Sentiment flips to fear as markets tumble"
    ]

    for t in tests:
        p = route_persona_for_headline(t)
        print(f"{t}  →  {p}")

