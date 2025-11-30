#!/usr/bin/env python3
"""
TOKNNews — Synthesis Engine (Deterministic Mode)

This module provides a single function:
    build_synthesis(headline, cluster_articles)

It produces a safe, concise, deterministic summary
that blends the headline with optional cluster articles.
"""

import re

def _clean(text: str) -> str:
    if not text:
        return ""
    return " ".join(text.split()).strip()


def _extract_keywords(text: str):
    """
    Deterministic keyword scoring for synthesis.
    NOT semantic — strictly deterministic token matching.
    """
    if not text:
        return []

    text = text.lower()
    keys = []

    KEYWORDS = [
        "bitcoin", "btc",
        "ethereum", "eth",
        "solana", "sol",
        "etf", "inflation", "rates",
        "regulation", "sec", "lawsuit",
        "yield", "liquidity", "staking",
        "volatility", "volume"
    ]

    for k in KEYWORDS:
        if k in text:
            keys.append(k)

    return list(dict.fromkeys(keys))  # unique, deterministic order


def build_synthesis(headline: str, cluster_articles: list):
    """
    Deterministic synthesis runner.

    headline          = main headline text
    cluster_articles  = list of related headlines (optional)

    Returns a short, safe, deterministic summary string.
    """

    if not headline:
        return "Market conditions and sentiment remain in focus."

    headline_clean = _clean(headline)

    # Extract keywords from headline
    kw_main = _extract_keywords(headline_clean)

    # Extract keywords from cluster
    kw_cluster = []
    for art in (cluster_articles or []):
        kw_cluster.extend(_extract_keywords(str(art)))

    # Unique + deterministic merge
    keyword_union = list(dict.fromkeys(kw_main + kw_cluster))

    # Build deterministic synthesis
    if keyword_union:
        core = ", ".join(keyword_union)
        base = f"This relates to ongoing activity around {core}."
    else:
        base = "This ties into broader market movement and sentiment."

    # Add short deterministic follow-up
    if len(cluster_articles or []) > 0:
        base += " Additional related developments are contributing to this trend."

    return base
