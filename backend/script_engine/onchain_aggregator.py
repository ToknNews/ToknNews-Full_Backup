#!/usr/bin/env python3
"""
onchain_aggregator.py
ToknNews — On-chain Intelligence Extractor

Builds:
 - whale_volume
 - largest_tx
 - trending_tokens
 - smart_money_sentiment
 - volatility_pulse
"""

def build_onchain_summary(moralis_data=None, birdeye_data=None, trending=None):
    """
    Input: raw API results
    Output: normalized on-chain intelligence dict
    """

    summary = {
        "whale_volume": 0.0,
        "largest_tx": 0.0,
        "trending_tokens": trending or [],
        "smart_money": "",
        "volatility": 0.0,
    }

    # TODO: once APIs are connected, parse real data.
    # For now, use placeholder-safe defaults to avoid frontend crashes.

    # Placeholder smart money logic
    summary["smart_money"] = "Accumulation trends detected across L1 ecosystems."

    # Placeholder volatility pulse
    summary["volatility"] = 0.42

    return summary
