#!/usr/bin/env python3
"""
enrich_v2.py
ToknNews — Canonical Enrichment Engine (Transfer Brain v1.2)

Responsibilities:
 - Neutral one-sentence summary (ingest-safe)
 - Domain classification
 - Sentiment tagging
 - Anchor suggestion
 - Asset identification (strict)
 - FACT CAPSULE extraction (verifiable claims)
"""

import time
import os
import re
import uuid
import hashlib
from typing import List, Dict

from backend.runtime.vault_loader import load_secrets

# ---------------------------------------------------------------
# INGEST MODE FLAG
# ---------------------------------------------------------------
INGEST_FAST_MODE = True

# ---------------------------------------------------------------
# DOMAIN MAP
# ---------------------------------------------------------------

DOMAIN_MAP = {
    "macro":      ["fed", "inflation", "treasury", "rates", "yields"],
    "regulation": ["sec", "cftc", "lawsuit", "hearing", "regulator", "irs"],
    "markets":    ["btc", "bitcoin", "eth", "ethereum", "price", "market", "rally", "selloff", "volume"],
    "defi":       ["defi", "staking", "liquidity", "aave", "uniswap"],
    "onchain":    ["onchain", "bridge", "exploit", "hack", "validator", "wallet"],
    "ai":         ["ai", "compute", "gpu", "nvidia", "model"],
    "culture":    ["memecoin", "viral", "trend", "doge", "community"],
    "general":    [],
}

def detect_domain(headline: str) -> str:
    h = headline.lower()
    for domain, words in DOMAIN_MAP.items():
        if any(w in h for w in words):
            return domain
    return "general"

# ---------------------------------------------------------------
# ASSET MAP (STRICT, NO GUESSING)
# ---------------------------------------------------------------

KNOWN_ASSETS = {
    "BTC": {
        "aliases": ["bitcoin", "btc"],
        "chain": "eth",
        "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"
    },
    "ETH": {
        "aliases": ["ethereum", "eth"],
        "chain": "eth",
        "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    },
    "SOL": {
        "aliases": ["solana", "sol"],
        "chain": "sol",
        "address": "So11111111111111111111111111111111111111112"
    }
}

def detect_asset(text: str):
    t = text.lower()
    for symbol, meta in KNOWN_ASSETS.items():
        if re.search(rf'(^|[^a-z0-9]){symbol.lower()}([^a-z0-9]|$)', t):
            return {"symbol": symbol, **meta}
        for alias in meta["aliases"]:
            if re.search(rf'(^|[^a-z0-9]){alias}([^a-z0-9]|$)', t):
                return {"symbol": symbol, **meta}
    return None

# ---------------------------------------------------------------
# SUMMARY (INGEST-SAFE)
# ---------------------------------------------------------------

def summarize(headline: str) -> str:
    return f"{headline.strip()}."

# ---------------------------------------------------------------
# SENTIMENT (LIGHTWEIGHT)
# ---------------------------------------------------------------

POS_WORDS = ["surges", "rises", "jumps", "soars", "growth", "up"]
NEG_WORDS = ["falls", "drops", "down", "crash", "tumbles", "decline"]

def get_sentiment(headline: str) -> str:
    h = headline.lower()
    if any(w in h for w in POS_WORDS):
        return "bullish"
    if any(w in h for w in NEG_WORDS):
        return "bearish"
    return "neutral"

# ---------------------------------------------------------------
# ANCHOR SUGGESTION
# ---------------------------------------------------------------

ANCHORS = {
    "macro":      ["bond"],
    "regulation": ["lawson"],
    "markets":    ["cash", "chip"],
    "defi":       ["reef"],
    "onchain":    ["ledger", "reef"],
    "ai":         ["neura"],
    "culture":    ["bitsy"],
    "general":    ["chip"],
}

def choose_anchors(domain: str):
    return ANCHORS.get(domain, ["chip"])

# ---------------------------------------------------------------
# FACT CAPSULE EXTRACTION (NEW)
# ---------------------------------------------------------------

def extract_fact_capsules(story: Dict) -> List[Dict]:
    """
    Extract verifiable fact capsules from enriched story.
    """
    capsules = []
    now = int(time.time())

    symbol = story.get("symbol")
    domain = story.get("domain")
    headline = story.get("headline", "")

    # -----------------------------
    # MARKET FACT
    # -----------------------------
    if domain == "markets" and symbol:
        capsules.append({
            "id": f"fc_{uuid.uuid4().hex[:8]}",
            "domain": "markets",
            "topic": "market_signal",
            "entity": {
                "symbol": symbol,
                "name": symbol,
                "type": "token"
            },
            "metric": {
                "label": "Market reaction event",
                "value": 1,
                "unit": "event",
                "direction": "neutral",
                "delta_pct": 0,
                "window": "current"
            },
            "source": {
                "provider": "enrich_v2",
                "origin": story.get("source"),
                "confidence": 0.6
            },
            "timestamp": now,
            "verbatim": headline,
            "use_cases": ["on_air", "pd_weighting"]
        })

    # -----------------------------
    # REGULATORY FACT
    # -----------------------------
    if domain == "regulation":
        capsules.append({
            "id": f"fc_{uuid.uuid4().hex[:8]}",
            "domain": "regulation",
            "topic": "policy_event",
            "entity": {
                "symbol": symbol,
                "name": "US Regulation",
                "type": "regulation"
            },
            "metric": {
                "label": "Regulatory action",
                "value": 1,
                "unit": "event",
                "direction": "neutral",
                "delta_pct": 0,
                "window": "current"
            },
            "source": {
                "provider": "enrich_v2",
                "origin": story.get("source"),
                "confidence": 0.7
            },
            "timestamp": now,
            "verbatim": headline,
            "use_cases": ["on_air"]
        })

    return capsules

def extract_onchain_capsule(story: Dict) -> Dict | None:
    """
    Build an on-chain fact capsule from Moralis-enriched data.
    Requires enrich_story() to have attached market_data.
    """
    md = story.get("market_context") or {}
    symbol = story.get("symbol")

    if not md or not symbol:
        return None

    net_flow = md.get("net_exchange_flow")
    if net_flow is None:
        return None

    direction = "outflow" if net_flow < 0 else "inflow"

    return {
        "id": f"fc_{uuid.uuid4().hex[:8]}",
        "domain": "onchain",
        "topic": "liquidity_shift",
        "entity": {
            "symbol": symbol,
            "chain": story.get("chain"),
            "type": "token"
        },
        "metric": {
            "label": "Net exchange flow",
            "value": abs(net_flow),
            "unit": symbol,
            "direction": direction,
            "delta_pct": md.get("flow_change_pct", 0),
            "window": "24h"
        },
        "participants": {
            "wallets": md.get("active_wallets", 0),
            "classification": "large holders" if md.get("whale_ratio", 0) > 0.6 else "mixed",
            "confidence": md.get("confidence", 0.7)
        },
        "source": {
            "provider": "moralis",
            "endpoint": "erc20/transfers",
            "confidence": md.get("confidence", 0.7)
        },
        "timestamp": int(time.time()),
        "verbatim": md.get("summary", ""),
        "use_cases": ["on_air", "pd_weighting"]
    }

# ---------------------------------------------------------------
# FACT CAPSULE (ANTI-REUSE CONTROL)
# ---------------------------------------------------------------

def build_fact_capsule(headline: str, summary: str, sentiment: str):
    base_string = f"{headline}|{summary}|{sentiment}"
    novelty_hash = hashlib.sha1(base_string.encode()).hexdigest()

    return {
        "primary_entity": None,
        "claim_type": "data",
        "timestamp": int(time.time()),
        "facts": [headline],
        "numeric_values": {},
        "novelty_hash": novelty_hash
    }

# ---------------------------------------------------------------
# MAIN ENRICH FUNCTION
# ---------------------------------------------------------------

def enrich_item(raw: dict) -> dict:
    headline = raw.get("headline", "").strip()
    ts = raw.get("timestamp", time.time())

    domain = detect_domain(headline)
    summary = summarize(headline)
    sentiment = get_sentiment(headline)
    anchors = choose_anchors(domain)

    enriched = {
        "headline": headline,
        "summary": summary,
        "narrative_seed": summary,
        "domain": domain,
        "sentiment": sentiment,
        "importance": 5,
        "anchors": anchors,
        "source": raw.get("source", "RSS"),
        "timestamp": ts
    }

    # Attach asset identity (if detected)
    asset = detect_asset(f"{headline} {summary}")
    if asset:
        enriched.update(asset)

    # -------------------------------------------------------
    # 🔑 PRODUCTION FACT CAPSULE (ANTI-REUSE CONTROL)
    # -------------------------------------------------------
    fact_capsule = build_fact_capsule(
        headline=headline,
        summary=summary,
        sentiment=sentiment
    )

    enriched["fact_capsule"] = fact_capsule

    return enriched


# Backward compatibility
def enrich_story(raw):
    return enrich_item(raw)

# ---------------------------------------------------------------
# TEST
# ---------------------------------------------------------------

if __name__ == "__main__":
    test = {
        "headline": "Bitcoin price falls as liquidity tightens",
        "source": "Marketaux",
        "timestamp": time.time()
    }
    print(enrich_item(test))
