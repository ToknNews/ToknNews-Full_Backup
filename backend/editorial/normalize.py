#!/usr/bin/env python3
"""
normalize.py — Editorial Engine v4

Purpose:
    Convert ANY raw ingestion object (RSS, API, On-chain signals)
    into a unified, guaranteed-safe dictionary.

Normalization guarantees:
    - headline: str
    - timestamp: float
    - source: str
    - raw_signals: dict
    - body: optional
    - metadata: passthrough for ingestion details

This keeps ALL downstream modules stable:
    - domain_classifier
    - memory_extractor
    - signal_fusion
    - editorial_gpt
"""

import time
from typing import Dict, Any


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _clean_str(x: Any) -> str:
    if not x:
        return ""
    if isinstance(x, (int, float)):
        return str(x)
    return str(x).strip()


def _safe_timestamp(x: Any) -> float:
    try:
        x = float(x)
        if x > 1000000000:  # already a UNIX timestamp
            return x
    except:
        pass
    return time.time()


def _extract_signals(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ingest v2 enrichers attach signals in different shapes.
    This normalizer ensures a unified container.
    """
    if not isinstance(raw, dict):
        return {}

    out = {}

    # Price / market data
    if "price" in raw:
        out["price"] = raw.get("price", {})

    # Volume
    if "volume" in raw:
        out["volume"] = raw.get("volume", {})

    # Whale alerts
    if "whales" in raw:
        out["whales"] = raw.get("whales", [])

    # Gas usage (eth/sol)
    if "gas" in raw:
        out["gas"] = raw.get("gas", {})

    # Liquidity stress
    if "liquidity" in raw:
        out["liquidity"] = raw.get("liquidity", {})

    # Additional ingestion metadata
    if "extra_signals" in raw:
        out.update(raw.get("extra_signals", {}))

    return out


# ------------------------------------------------------------
# Main function
# ------------------------------------------------------------

def normalize_item(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Accepts a raw ingestion dictionary and outputs a clean normalized story.
    """

    if not isinstance(raw, dict):
        raw = {"headline": str(raw)}

    headline = _clean_str(raw.get("headline") or raw.get("title") or "")

    if not headline:
        headline = "Untitled Story"

    normalized = {
        "headline": headline,
        "body": _clean_str(raw.get("body") or raw.get("description") or ""),
        "timestamp": _safe_timestamp(raw.get("timestamp")),
        "source": _clean_str(raw.get("source") or raw.get("feed") or "unknown"),
        "url": _clean_str(raw.get("url")),
        "raw_signals": _extract_signals(raw),
        "metadata": {
            "original": raw
        }
    }

    return normalized


# ------------------------------------------------------------
# Self-test
# ------------------------------------------------------------
if __name__ == "__main__":
    example = {
        "headline": "BTC surges 5% on ETF demand",
        "price": {"pct_change": 5.1},
        "volume": {"delta": 3.2},
        "whales": ["0xabc sent 5000 BTC"],
        "gas": {"gwei": 90},
        "timestamp": 1765239293,
        "source": "coindesk"
    }

    print("\n=== NORMALIZED RESULT ===")
    print(normalize_item(example))
