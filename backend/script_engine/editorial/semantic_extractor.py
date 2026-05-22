#!/usr/bin/env python3
"""
semantic_extractor.py
ToknNews — Semantic Extraction Layer (STEP 3B)

Responsibilities:
- Extract structured meaning from a single story
- NO clustering
- NO narrative generation
- Deterministic first, heuristic second
"""

from __future__ import annotations
from typing import Dict, Any, List
import re
import time

# --------------------------------------------------
# ASSET REGEX (expandable)
# --------------------------------------------------

ASSET_REGEX = re.compile(
    r"\b(BTC|BITCOIN|ETH|ETHEREUM|SOL|SOLANA|BNB|AVAX|AAVE|ARB|OP|XRP|DOGE)\b",
    re.IGNORECASE
)

# --------------------------------------------------
# EVENT TYPE HEURISTICS
# --------------------------------------------------

EVENT_KEYWORDS = {
    "price_breakout": [
        "hits", "breaks", "crosses", "surges", "rallies", "soars", "ath"
    ],
    "price_decline": [
        "drops", "falls", "slides", "tumbles", "crashes"
    ],
    "regulation": [
        "sec", "regulation", "law", "court", "lawsuit", "compliance"
    ],
    "institutional_flow": [
        "etf", "blackrock", "fidelity", "institutional", "fund inflow"
    ],
    "onchain_activity": [
        "whale", "transfer", "liquidation", "on-chain"
    ],
    "protocol_update": [
        "upgrade", "proposal", "hard fork", "governance"
    ],
    "asset_trend": [
        "trending", "coingecko", "top mover"
    ]
}

# --------------------------------------------------
# ACTOR HEURISTICS
# --------------------------------------------------

ACTOR_KEYWORDS = {
    "institutions": ["blackrock", "fidelity", "vanguard", "institutional"],
    "traders": ["trader", "speculator", "whale"],
    "regulators": ["sec", "court", "government", "regulator"],
    "developers": ["dev", "developer", "core team"]
}

# --------------------------------------------------
# CORE EXTRACTION
# --------------------------------------------------

def extract_semantic_keys(story: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract semantic meaning from a single story.
    """

    headline = (story.get("headline") or "").lower()
    summary  = (story.get("summary") or "").lower()
    text     = f"{headline} {summary}"

    # ---------------------------
    # Assets
    # ---------------------------
    assets = sorted(set(
        m.group(1).upper()
        for m in ASSET_REGEX.finditer(text)
    ))

    # ---------------------------
    # Event type
    # ---------------------------
    event_type = "unknown"
    for evt, keywords in EVENT_KEYWORDS.items():
        if any(k in text for k in keywords):
            event_type = evt
            break

    # ---------------------------
    # Actors
    # ---------------------------
    actors: List[str] = []
    for actor, keys in ACTOR_KEYWORDS.items():
        if any(k in text for k in keys):
            actors.append(actor)

    # ---------------------------
    # Time scope
    # ---------------------------
    published_at = story.get("published_at")
    now = time.time()

    if published_at:
        try:
            delta = now - float(published_at)
            time_scope = "immediate" if delta < 6 * 3600 else "recent"
        except Exception:
            time_scope = "unknown"
    else:
        time_scope = "unknown"

    # ---------------------------
    # Confidence score (simple heuristic)
    # ---------------------------
    confidence = 0.3
    if assets:
        confidence += 0.2
    if event_type != "unknown":
        confidence += 0.3
    if actors:
        confidence += 0.2

    confidence = min(confidence, 1.0)

    return {
        "domain": story.get("domain", "general"),
        "assets": assets,
        "event_type": event_type,
        "actors": actors,
        "time_scope": time_scope,
        "confidence": round(confidence, 2)
    }
