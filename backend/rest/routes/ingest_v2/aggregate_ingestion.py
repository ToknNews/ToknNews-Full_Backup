#!/usr/bin/env python3
"""
aggregate_ingestion.py
ToknNews — Aggregator + Fact Capsule Builder (V2-safe)

Responsibilities:
- De-duplicate stories
- Normalize importance
- Preserve editorial substrate
- Build fact_capsules for downstream scripting
- Sort by recency

This layer DOES NOT:
- Decide breaking status
- Decide script structure
"""

import time
import uuid
from backend.script_engine.analytics_sqlite import narrative_recently_used


# ======================================================
# DEDUPLICATION
# ======================================================

def _dedupe(stories):
    seen = set()
    unique = []
    for s in stories:
        h = (s.get("headline") or "").strip()
        if h and h not in seen:
            seen.add(h)
            unique.append(s)
    return unique


# ======================================================
# IMPORTANCE NORMALIZATION
# ======================================================

def _apply_importance(item):
    importance = float(item.get("importance", 5))
    item["breaking"] = False
    item["importance"] = importance

    capsule = item.get("fact_capsule")
    if capsule:
        novelty_hash = capsule.get("novelty_hash")
        if novelty_hash and narrative_recently_used(novelty_hash):
            item["importance"] = 0.1  # suppress reuse

    return item


# ======================================================
# FACT CAPSULE BUILDER (NEW)
# ======================================================

def _build_fact_capsules(item):
    """
    Builds evidence-backed fact capsules from existing data.
    No inference, no hallucination.
    """
    capsules = []

    ts = item.get("timestamp", int(time.time()))
    entities = item.get("entities") or []
    grok = item.get("grok_enrichment") or {}
    market_ctx = item.get("market_context") or {}

    # -----------------------------
    # ENTITY-BASED CAPSULES
    # -----------------------------
    for e in entities:
        mentions = e.get("mentions", 0)
        sentiment = e.get("sentiment_score")

        if mentions and mentions >= 3:
            capsules.append({
                "capsule_id": str(uuid.uuid4()),
                "type": "entity_attention",
                "confidence": "high" if mentions >= 8 else "medium",
                "time_window": "72h",
                "entities": [{
                    "name": e.get("name"),
                    "symbol": e.get("symbol"),
                    "role": "market_entity"
                }],
                "claim": f"Increased market attention around {e.get('name')}",
                "evidence": [
                    f"{mentions} mentions across recent coverage"
                ],
                "metrics": {
                    "mentions": mentions,
                    "sentiment": sentiment
                },
                "implication": item.get("implication"),
                "why_it_matters": (
                    "Sustained attention often precedes positioning or volatility shifts"
                ),
                "source_refs": [{
                    "source": item.get("source"),
                    "url": item.get("link")
                }],
                "anchor_hint": "State as confirmation, not prediction",
                "timestamp": ts
            })

    # -----------------------------
    # GROK FACT CAPSULES
    # -----------------------------
    if grok and isinstance(grok, dict):
        facts = grok.get("facts") or []
        implication = grok.get("implication")

        for f in facts[:2]:  # cap to avoid overload
            capsules.append({
                "capsule_id": str(uuid.uuid4()),
                "type": "verified_fact",
                "confidence": "high",
                "time_window": "24h",
                "entities": [],
                "claim": f,
                "evidence": ["Grok full-article analysis"],
                "metrics": {},
                "implication": implication,
                "why_it_matters": (
                    "Confirmed developments shape institutional expectations"
                ),
                "source_refs": [{
                    "source": item.get("source"),
                    "url": item.get("link")
                }],
                "anchor_hint": "Frame as established fact",
                "timestamp": ts
            })

    # -----------------------------
    # MARKET CONTEXT CAPSULES
    # -----------------------------
    if market_ctx:
        capsules.append({
            "capsule_id": str(uuid.uuid4()),
            "type": "market_context",
            "confidence": "medium",
            "time_window": "24h",
            "entities": [],
            "claim": "Market context provides backdrop for current price action",
            "evidence": ["CoinGecko market context"],
            "metrics": market_ctx,
            "implication": item.get("implication"),
            "why_it_matters": (
                "Context helps distinguish rotation from genuine risk appetite"
            ),
            "source_refs": [{
                "source": "coingecko",
                "url": None
            }],
            "anchor_hint": "Use to frame discussion, not as headline",
            "timestamp": ts
        })

    return capsules


# ======================================================
# MAIN AGGREGATION ENTRYPOINT
# ======================================================

def aggregate_items(stories):
    if not stories:
        return []

    deduped = _dedupe(stories)

    processed = []
    for s in deduped:
        s = _apply_importance(s)
        s["fact_capsules"] = _build_fact_capsules(s)
        processed.append(s)

    processed.sort(key=lambda x: x.get("timestamp", 0), reverse=True)
    return processed


# ======================================================
# CLI TEST
# ======================================================

if __name__ == "__main__":
    print("[AGG] Aggregator + fact_capsules ready.")
