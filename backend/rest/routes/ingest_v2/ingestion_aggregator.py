#!/usr/bin/env python3
"""
ingestion_aggregator.py  
TOKEN NEWS — Rolling Memory + Freshness + Dedupe Engine (2025 Rebuild)

Responsibilities:
 - Combine RSS + API enriched stories
 - Merge Moralis + RPC lightweight signals
 - Deduplicate stories (headline + summary hash)
 - Apply 12h freshness filter
 - Maintain 48h rolling memory
 - Produce final “fresh list” for episode_builder
"""

import os
import json
import time
from hashlib import md5

ROLLING_PATH = "/opt/toknnews/data/rolling_stories.json"

FRESHNESS_WINDOW  = 12 * 3600   # 12 hours
MEMORY_WINDOW     = 48 * 3600   # 48 hours


# ============================================================
# LOAD + SAVE
# ============================================================

def load_rolling():
    if not os.path.exists(ROLLING_PATH):
        return []
    try:
        with open(ROLLING_PATH, "r") as f:
            return json.load(f)
    except:
        return []


def save_rolling(data):
    try:
        with open(ROLLING_PATH, "w") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print("[Aggregator] ERROR saving rolling:", e)


# ============================================================
# DEDUPE
# ============================================================

def story_fingerprint(headline, summary):
    """Hash headline+summary to dedupe identical stories."""
    payload = (headline or "") + "|" + (summary or "")
    return md5(payload.encode()).hexdigest()


def dedupe(stories):
    seen = set()
    out = []
    for s in stories:
        fp = story_fingerprint(s.get("headline"), s.get("summary"))
        if fp not in seen:
            seen.add(fp)
            out.append(s)
    return out


# ============================================================
# SIGNALS MERGE (Moralis + RPC)
# ============================================================

def merge_signals(stories, whales, liquidations, rpc_block, rpc_gas):
    """
    Lightweight influence on volatility + importance.
    We don't rewrite stories; we gently boost their scores.
    """

    # Whale → market-moving → slight importance bump
    if whales:
        for s in stories:
            s["importance"] = min(s["importance"] + 0.2, 10)

    # Liquidations → defi/markets spikes
    if liquidations:
        for s in stories:
            if s["domain"] in ["defi", "markets"]:
                s["volatility"] += 0.5

    # RPC gas spike = onchain stress
    try:
        if rpc_gas:
            gas_int = int(rpc_gas, 16)
            if gas_int > 200e9:  # high congestion
                for s in stories:
                    if s["domain"] in ["onchain", "defi"]:
                        s["volatility"] += 0.3
    except:
        pass

    return stories


# ============================================================
# FRESHNESS FILTER
# ============================================================

def filter_fresh(stories):
    now = time.time()
    return [
        s for s in stories
        if now - float(s.get("timestamp", now)) <= FRESHNESS_WINDOW
    ]


# ============================================================
# ROLLING WINDOW FILTER
# ============================================================

def filter_memory(stories):
    now = time.time()
    return [
        s for s in stories
        if now - float(s.get("timestamp", now)) <= MEMORY_WINDOW
    ]


# ============================================================
# MAIN AGGREGATION LOGIC
# ============================================================

def aggregate_ingestion(
    enriched_rss_items,
    enriched_api_items,
    moralis_whales=None,
    moralis_liquidations=None,
    rpc_block=None,
    rpc_gas=None
):
    """
    Combine → Merge Signals → Dedupe → Fresh Filter → Update Rolling Memory
    """

    rolling = load_rolling()

    # Combine new items
    combined = enriched_rss_items + enriched_api_items

    # Dedupe new
    combined = dedupe(combined)

    # Merge chain signals
    combined = merge_signals(
        combined,
        moralis_whales,
        moralis_liquidations,
        rpc_block,
        rpc_gas
    )

    # Fresh items for this cycle
    fresh = filter_fresh(combined)

    # Update rolling memory
    updated_memory = dedupe(filter_memory(rolling + fresh))
    save_rolling(updated_memory)

    return fresh, updated_memory
