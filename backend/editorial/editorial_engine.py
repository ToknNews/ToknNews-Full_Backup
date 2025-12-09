#!/usr/bin/env python3
"""
editorial_engine.py — ToknNews Editorial Engine v4
Master orchestrator for story enrichment.

Pipeline:
    1. normalize(item)
    2. classify_domain(normalized)
    3. extract_memory(normalized)
    4. fuse_signals(normalized + memory)
    5. summarize_story(normalized + memory + signals)

Output:
A complete enriched editorial-ready dict:
{
    headline: str,
    summary: str,
    domain: str,
    signals: {...},
    memory: {...},
    anchors: [...],
    timestamp: float,
    source: "RSS" | "API" | "ONCHAIN"
}
"""

import time

from editorial.normalize import normalize
from editorial.domain_classifier import classify_domain
from editorial.memory_extractor import extract_memory
from editorial.signal_fusion import fuse_signals
from editorial.editorial_gpt import summarize_story


# ----------------------------------------------------------------------
# MASTER ENRICH FUNCTION
# ----------------------------------------------------------------------

def enrich(item):
    """
    Takes a raw ingestion item and returns a fully enriched story.
    """
    # 1) Normalize
    norm = normalize(item)

    # 2) Domain classification
    domain = classify_domain(norm)
    norm["domain"] = domain

    # 3) Editorial memory extraction
    memory = extract_memory(norm)
    norm["memory"] = memory

    # 4) Signal fusion (onchain + sentiment + metadata)
    signals = fuse_signals(norm, memory)
    norm["signals"] = signals

    # 5) GPT summarization (2–4 sentence editorial summary)
    gpt = summarize_story(norm)
    norm["summary"] = gpt.get("summary", "")
    norm["confidence"] = gpt.get("confidence", 0.0)

    # 6) Auto-anchor selection (domain → likely persona)
    #    This can later be replaced with a smarter model.
    norm["anchors"] = _anchors_for_domain(domain)

    # 7) Timestamp if missing
    if "timestamp" not in norm:
        norm["timestamp"] = time.time()

    return norm


# ----------------------------------------------------------------------
# Domain → Anchors mapping (simple deterministic seed)
# ----------------------------------------------------------------------

ANCHOR_MAP = {
    "defi":        ["reef"],
    "onchain":     ["ledger"],
    "markets":     ["bond", "cash"],
    "macro":       ["bond"],
    "regulation":  ["lawson"],
    "sentiment":   ["ivy", "cash"],
    "culture":     ["bitsy", "penny"],
    "ai":          ["neura"],
    "general":     ["chip"]
}

def _anchors_for_domain(domain):
    return ANCHOR_MAP.get(domain, ["chip"])


# ----------------------------------------------------------------------
# Batch utility
# ----------------------------------------------------------------------

def enrich_batch(items):
    enriched = []
    for item in items:
        try:
            enriched.append(enrich(item))
        except Exception as e:
            print("[EditorialEngine] ERROR enriching item:", e)
    return enriched


# ----------------------------------------------------------------------
# Self-test
# ----------------------------------------------------------------------

if __name__ == "__main__":
    demo = {
        "headline": "Bitcoin spikes as whales move $200M in one hour",
        "source": "API",
        "body": "",
        "onchain": {
            "whales": 4,
            "netflow": -180_000_000,
            "gas": 35
        }
    }

    out = enrich(demo)

    print("\n=== EDITORIAL ENGINE v4 OUTPUT ===")
    for k, v in out.items():
        print(f"{k}: {v}")
