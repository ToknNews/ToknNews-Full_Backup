#!/usr/bin/env python3
"""
signal_fusion.py — Editorial Engine v4

Fuses all quant-style signals from ingest_v2 into a unified
editorial signal block suitable for summary GPT + PD routing.

Input (from enrich_v4):
story["raw_signals"] = {
    "price":      {"pct_change": ...},
    "volume":     {"delta": ...},
    "whales":     [...],
    "gas":        {"gwei": ...},
    "liquidity":  {"stress": ...},
    "sentiment":  {"score": ...},
    "onchain":    {... more structured data ...}
}

Output (fused):
{
   "price_trend": "up|down|flat",
   "volume_spike": bool,
   "whale_activity": bool,
   "gas_pressure": bool,
   "liquidity_pressure": bool,
   "sentiment_shift": "bullish|bearish|neutral",
   "composite_heat": 0–10,
   "flags": {
       "stress_event": bool,
       "breakout_event": bool,
       "whale_attention": bool,
       "onchain_migration": bool
   }
}

Optional GPT "signal commentary" is supported but OFF by default.
"""

from typing import Dict, Any


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _trend(v: float) -> str:
    if v > 2.5:   return "up"
    if v < -2.5:  return "down"
    return "flat"


def _sentiment_shift(score: float) -> str:
    if score > 0.25:   return "bullish"
    if score < -0.25:  return "bearish"
    return "neutral"


def _bool(x: Any) -> bool:
    return x is not None and x not in ("", 0, False) and bool(x)


# ------------------------------------------------------------
# Fusion Engine
# ------------------------------------------------------------

def fuse_signals(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge all structured quant signals.
    """

    if not raw:
        return {
            "price_trend": "flat",
            "volume_spike": False,
            "whale_activity": False,
            "gas_pressure": False,
            "liquidity_pressure": False,
            "sentiment_shift": "neutral",
            "composite_heat": 0,
            "flags": {}
        }

    price_delta = raw.get("price", {}).get("pct_change", 0)
    volume_delta = raw.get("volume", {}).get("delta", 0)
    whales = raw.get("whales", [])
    gas = raw.get("gas", {}).get("gwei", 0)
    liquidity = raw.get("liquidity", {}).get("stress", 0)
    sentiment_score = raw.get("sentiment", {}).get("score", 0)
    onchain = raw.get("onchain", {}) or {}

    out = {}

    # --------------------------------------------
    # Price Trend
    # --------------------------------------------
    out["price_trend"] = _trend(price_delta)

    # --------------------------------------------
    # Volume Spike
    # --------------------------------------------
    out["volume_spike"] = abs(volume_delta) > 2.0

    # --------------------------------------------
    # Whale Activity
    # --------------------------------------------
    out["whale_activity"] = len(whales) > 0

    # --------------------------------------------
    # Gas Pressure
    # --------------------------------------------
    out["gas_pressure"] = gas > 120  # threshold adjustable

    # --------------------------------------------
    # Liquidity Pressure
    # --------------------------------------------
    out["liquidity_pressure"] = liquidity > 0.5

    # --------------------------------------------
    # Sentiment shift
    # --------------------------------------------
    out["sentiment_shift"] = _sentiment_shift(sentiment_score)

    # --------------------------------------------
    # Composite Heat Score
    # --------------------------------------------
    heat = 0
    heat += 2 if out["price_trend"] == "down" else 0
    heat += 2 if out["volume_spike"] else 0
    heat += 2 if out["whale_activity"] else 0
    heat += 2 if out["gas_pressure"] else 0
    heat += 2 if out["liquidity_pressure"] else 0

    # softer heat based on sentiment
    if out["sentiment_shift"] == "bearish":
        heat += 1
    if out["sentiment_shift"] == "bullish":
        heat = max(0, heat - 1)

    out["composite_heat"] = min(10, heat)

    # --------------------------------------------
    # Flag generation for PD & memory arcs
    # --------------------------------------------
    out["flags"] = {
        "stress_event": out["composite_heat"] >= 6,
        "breakout_event": (out["price_trend"] == "up" and out["volume_spike"]),
        "whale_attention": out["whale_activity"],
        "onchain_migration": bool(onchain.get("flows", {}).get("migration")),
    }

    return out


# ------------------------------------------------------------
# Standalone demo (optional)
# ------------------------------------------------------------
if __name__ == "__main__":
    example = {
        "price": {"pct_change": -4.8},
        "volume": {"delta": 6.3},
        "whales": ["0xabc moved 20,000 SOL"],
        "gas": {"gwei": 140},
        "liquidity": {"stress": 0.72},
        "sentiment": {"score": -0.31},
        "onchain": {"flows": {"migration": True}}
    }

    print("\n=== FUSED SIGNAL OUTPUT ===")
    print(fuse_signals(example))
