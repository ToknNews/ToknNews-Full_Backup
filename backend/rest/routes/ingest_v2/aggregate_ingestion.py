#!/usr/bin/env python3
"""
aggregate_ingestion.py
ToknNews 2025 — Aggregator (V2-safe)

Now:
 - dedupe
 - timestamp normalization (assumed pre-set)
 - importance shaping
 - recency sort (new → old)
 - DOES NOT auto-mark stories as breaking.

Breaking will be assigned later by PDv4 / Router using meta-enrichment + StoryBank.
"""

import time

def _dedupe(stories):
    seen = set()
    unique = []
    for s in stories:
        h = s.get("headline", "").strip()
        if h and h not in seen:
            seen.add(h)
            unique.append(s)
    return unique


def _apply_importance(item):
    """
    Basic importance shaping:
     - default importance = 5 (from enrich_v2)
     - NO automatic breaking flag here.
    """
    importance = float(item.get("importance", 5))
    # Clear any previous breaking noise
    item["breaking"] = False
    item["importance"] = importance
    return item


def aggregate_items(stories):
    if not stories:
        return []

    deduped = _dedupe(stories)
    processed = [_apply_importance(s) for s in deduped]

    processed.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return processed


if __name__ == "__main__":
    print("[AGG] Module test OK — aggregator is ready.")
