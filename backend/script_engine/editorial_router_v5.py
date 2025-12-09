#!/usr/bin/env python3
"""
editorial_router_v5.py
ToknNews — Editorial Engine v4 Router (Unified Entry Point)

This module replaces all of:
 - enrich_v2.py
 - meta_enrich.py
 - light_gpt_enrichers
 - manual domain classifiers

All ingestion systems should now call:
    from script_engine.editorial_router_v5 import enrich_story

The output is a fully enriched story dict ready for:
 - PD Engine v4
 - Timeline Builder v5
 - show_modes
 - autonomous broadcast pipeline
"""

import time
from typing import Dict, Any

# Submodules (installed earlier)
from script_engine.editorial_engine_v4.normalize import normalize_item
from script_engine.editorial_engine_v4.domain_classifier import classify_domain
from script_engine.editorial_engine_v4.memory_extractor import extract_memory
from script_engine.editorial_engine_v4.signal_fusion import fuse_signals
from script_engine.editorial_engine_v4.editorial_gpt import editorial_summarize

# Persona routing (from your existing system)
from script_engine.context_router import route_persona_for_headline


# ============================================================
# MASTER ENRICH FUNCTION
# ============================================================

def enrich_story(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    INPUT:
        raw ingestion item from ingest_v2 pipeline
        {
           headline: ...,
           body: ...,
           url: ...,
           timestamp: ...,
           raw_signals: {... onchain + quant signals ...}
           source: "RSS" | "API" | ...
        }

    OUTPUT:
        enriched ToknStory dict
        {
           headline: str
           summary: str (GPT)
           domain: str
           memory: {entities, patterns}
           signals: fused_signal_dict
           persona_primary: str
           persona_secondary: str | None
           persona_tertiary: str | None
           anchors: [...]
           timestamp: float
           source: str
        }
    """

    # 1) Normalize
    story = normalize_item(raw)

    headline = story.get("headline", "").strip()
    body     = story.get("body", "") or ""

    # 2) Domain Classification
    domain = classify_domain(headline, body)
    story["domain"] = domain

    # 3) Editorial Memory Extraction
    memory = extract_memory(headline, body)
    story["memory"] = memory

    # 4) On-chain / Quant Signal Fusion
    fused_signals = fuse_signals(story.get("raw_signals", {}))
    story["signals"] = fused_signals

    # 5) GPT Summary (Editorial-grade)
    story["summary"] = editorial_summarize(
        headline=headline,
        body=body,
        domain=domain,
        memory=memory,
        signals=fused_signals
    )

    # 6) Persona Routing (determine who covers this)
    primary = route_persona_for_headline(headline)
    secondary = None
    tertiary = None

    # Late-night looseness or multi-anchor logic will be applied in PDv4

    anchors = [primary]
    if secondary:
        anchors.append(secondary)
    if tertiary:
        anchors.append(tertiary)

    story["persona_primary"] = primary
    story["persona_secondary"] = secondary
    story["persona_tertiary"] = tertiary
    story["anchors"] = anchors

    # Ensure timestamp
    story["timestamp"] = story.get("timestamp") or time.time()

    return story


# ============================================================
# BATCH ENTRY POINT (for ingest_v2)
# ============================================================

def enrich_batch(raw_items):
    """
    Takes a list of raw ingestion dicts and returns enriched stories.
    """
    enriched = []
    for item in raw_items:
        try:
            e = enrich_story(item)
            enriched.append(e)
        except Exception as exc:
            print(f"[EditorialRouter] ERROR enriching story: {exc}")
            continue
    return enriched


# ============================================================
# DEMO SELF-TEST
# ============================================================

if __name__ == "__main__":
    demo_raw = {
        "headline": "Solana gas spikes as whale wallets rotate positions",
        "body": "Several large wallets moved through Jupiter and Raydium...",
        "raw_signals": {
            "gas": {"gwei": 180},
            "whales": ["wallet1 moved 12k SOL"],
            "volume": {"delta": 3.2},
            "price": {"pct_change": -4.1},
        },
        "source": "API",
    }

    enriched = enrich_story(demo_raw)
    print("\n=== ENRICHED STORY ===")
    for k, v in enriched.items():
        print(f"{k}: {v}")
