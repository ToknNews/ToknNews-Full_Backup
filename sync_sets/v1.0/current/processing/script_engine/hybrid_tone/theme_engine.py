#!/usr/bin/env python3
"""
TOKNNews — Theme Engine (Strict Deterministic Mode)
Extracts a single structured theme from headline + synthesis.
"""

import re

# Keyword maps define deterministic theme inference
THEME_MAP = {
    "bitcoin": "bitcoin momentum and network dynamics",
    "btc": "bitcoin momentum and network dynamics",
    "ethereum": "ethereum ecosystem and smart contract flows",
    "eth": "ethereum ecosystem and smart contract flows",
    "solana": "solana performance and validator activity",
    "sol": "solana performance and validator activity",
    "etf": "institutional positioning and market structure",
    "regulation": "regulatory pressure and compliance impact",
    "sec": "regulatory pressure and compliance impact",
    "lawsuit": "legal exposure and litigation risk",
    "yield": "yield pressure and liquidity incentives",
    "inflation": "macro inflation effects and rate sensitivity",
    "interest": "macro interest-rate expectations",
    "stablecoin": "stablecoin liquidity and peg confidence",
    "defi": "defi protocol flows and risk concentration",
    "exchange": "exchange activity and liquidity conditions",
    "staking": "staking flows and validator economics",
    "volatility": "market volatility and sentiment rotation",
    "hack": "security exposure and exploit impact",
    "exploit": "security exposure and exploit impact"
}


def extract_theme(text: str) -> str:
    """
    Deterministic keyword → theme mapping.
    Falls back to simple market-context theme.
    """
    if not text:
        return "market context and recent developments"

    lower = text.lower()

    for key, theme in THEME_MAP.items():
        if key in lower:
            return theme

    # Fallback deterministic theme
    return "market conditions and evolving sentiment"
