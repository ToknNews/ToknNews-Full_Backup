#!/usr/bin/env python3
"""
stage3_enricher.py
ToknNews 2025 — Stage 3 Enrichment (Transfer Brain v1.0 baseline)

Purpose:
 - Optional final tweak to enriched stories.
 - NO external API calls in baseline (avoid blocking).
 - Light importance shaping based on domain/sentiment.
"""

def stage3_enrich(item: dict) -> dict:
    """
    Adjust importance slightly based on domain + sentiment.
    This is intentionally minimal and deterministic.
    """
    if not isinstance(item, dict):
        return item

    domain = item.get("domain", "general")
    sentiment = item.get("sentiment", "Neutral")
    importance = float(item.get("importance", 5))

    # Simple boosts
    if domain in ("macro", "markets", "defi"):
        importance += 0.5

    if sentiment == "Negative":
        importance += 0.5  # negative risk often matters more

    item["importance"] = importance
    return item


if __name__ == "__main__":
    test = {
        "headline": "BTC drops on macro jitters",
        "domain": "markets",
        "sentiment": "Negative",
        "importance": 5,
    }
    print(stage3_enrich(test))
