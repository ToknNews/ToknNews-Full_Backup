#!/usr/bin/env python3
"""
TOKNNews — Comparative Engine (Strict Deterministic Mode)
Produces simple, safe comparative clauses for anchor analysis.
"""

import re

def comparative_wrap(text: str) -> str:
    """
    Returns a deterministic comparative statement using simple
    keyword grouping and safe fallback.
    """

    t = (text or "").lower()

    if "bitcoin" in t or "btc" in t:
        return "Compared with last week’s BTC flows, positioning remains steady."

    if "ethereum" in t or "eth" in t:
        return "Relative to recent ETH activity, network usage has been consistent."

    if "solana" in t or "sol" in t:
        return "Compared with prior Solana sessions, volume rotation is noticeable."

    if "etf" in t:
        return "Relative to ETF inflows earlier this month, sentiment remains directional."

    # fallback comparative
    return "Relative to recent sessions, conditions remain within expected ranges."
