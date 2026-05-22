#!/usr/bin/env python3
"""
signal_engine.py

ToknNews — Signals Engine (Canonical v2)

PURPOSE:
- Derive structured, narrative-safe signals from numeric enrichment
- Feed ESL with interpretation hints (never text)
- Support broadcast + verticals

INPUT:
- numeric_enrichment (canonical schema)

OUTPUT:
- List of signal objects
"""

from typing import Dict, Any, List
import statistics

# =========================================================
# THRESHOLDS (CONSERVATIVE, BROADCAST-SAFE)
# =========================================================

CONFIDENCE_FLOOR = 0.6

PRICE_FLAT_PCT = 1.0
PRICE_MOVE_PCT = 2.0

VOLUME_SPIKE_PCT = 15.0
VOLUME_DROP_PCT = -10.0

TX_TREND_UP = "up"
TX_TREND_DOWN = "down"

VOLATILITY_EXPANSION_PCT = 2.5
VOLATILITY_COMPRESSION_PCT = 0.8

# =========================================================
# BASE SIGNALS
# =========================================================

def detect_accumulation(data: Dict[str, Any]) -> Dict[str, Any] | None:
    price = data["price"]
    activity = data["activity"]
    liquidity = data.get("liquidity", {})

    if price["change_24h_pct"] is None:
        return None

    vol_change = liquidity.get("dex_volume_change_24h_pct")
    if vol_change is None:
        return None

    if abs(price["change_24h_pct"]) <= PRICE_FLAT_PCT and vol_change >= VOLUME_SPIKE_PCT:
        confidence = min(0.9, 0.6 + vol_change / 100)

        return {
            "signal_type": "accumulation",
            "confidence": round(confidence, 2),
            "chains": [data["chain"]],
            "evidence": {
                "price_change_24h_pct": price["change_24h_pct"],
                "volume_change_24h_pct": vol_change,
                "tx_trend": activity["tx_trend"],
            },
        }
    return None


def detect_distribution(data: Dict[str, Any]) -> Dict[str, Any] | None:
    price = data["price"]
    liquidity = data.get("liquidity", {})

    vol_change = liquidity.get("dex_volume_change_24h_pct")
    if price["change_24h_pct"] is None or vol_change is None:
        return None

    if price["change_24h_pct"] <= -PRICE_FLAT_PCT and vol_change >= VOLUME_SPIKE_PCT:
        return {
            "signal_type": "distribution",
            "confidence": 0.7,
            "chains": [data["chain"]],
            "evidence": {
                "price_change_24h_pct": price["change_24h_pct"],
                "volume_change_24h_pct": vol_change,
            },
        }
    return None


def detect_speculative_churn(data: Dict[str, Any]) -> Dict[str, Any] | None:
    liquidity = data.get("liquidity", {})
    activity = data["activity"]

    vol_change = liquidity.get("dex_volume_change_24h_pct")
    if vol_change is None:
        return None

    if vol_change <= VOLUME_DROP_PCT and activity["tx_trend"] == TX_TREND_UP:
        return {
            "signal_type": "speculative_churn",
            "confidence": 0.65,
            "chains": [data["chain"]],
            "evidence": {
                "volume_change_24h_pct": vol_change,
                "tx_trend": activity["tx_trend"],
            },
        }
    return None

# =========================================================
# CROSS-CHAIN SIGNALS
# =========================================================

def detect_capital_rotation(chains: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    volume_changes = {
        c: d["liquidity"]["dex_volume_change_24h_pct"]
        for c, d in chains.items()
        if d.get("liquidity", {}).get("dex_volume_change_24h_pct") is not None
    }

    if len(volume_changes) < 2:
        return None

    stdev = statistics.stdev(volume_changes.values())
    if stdev < 10:
        return None

    dominant = max(volume_changes, key=volume_changes.get)

    return {
        "signal_type": "capital_rotation",
        "confidence": round(min(0.9, 0.6 + stdev / 100), 2),
        "chains": list(volume_changes.keys()),
        "dominant_chain": dominant,
        "evidence": volume_changes,
    }


def detect_liquidity_migration(chains: Dict[str, Dict[str, Any]]) -> Dict[str, Any] | None:
    liquidity = {
        c: d["liquidity"]["dex_volume_change_24h_pct"]
        for c, d in chains.items()
        if d.get("liquidity", {}).get("dex_volume_change_24h_pct") is not None
    }

    if len(liquidity) < 2:
        return None

    max_chain = max(liquidity, key=liquidity.get)
    min_chain = min(liquidity, key=liquidity.get)

    if liquidity[max_chain] - liquidity[min_chain] >= 20:
        return {
            "signal_type": "liquidity_migration",
            "confidence": 0.75,
            "chains": [min_chain, max_chain],
            "evidence": liquidity,
        }
    return None


def detect_participation_shift(data: Dict[str, Any]) -> Dict[str, Any] | None:
    activity = data["activity"]
    liquidity = data.get("liquidity", {})

    vol_change = liquidity.get("dex_volume_change_24h_pct")
    if vol_change is None:
        return None

    if activity["tx_trend"] == TX_TREND_UP and vol_change < PRICE_FLAT_PCT:
        return {
            "signal_type": "participation_broadening",
            "confidence": 0.65,
            "chains": [data["chain"]],
            "evidence": {
                "tx_trend": activity["tx_trend"],
                "volume_change_24h_pct": vol_change,
            },
        }
    return None

# =========================================================
# MAIN ORCHESTRATOR
# =========================================================

def generate_signals(numeric_enrichment: Dict[str, Any]) -> List[Dict[str, Any]]:
    signals: List[Dict[str, Any]] = []
    chains = numeric_enrichment.get("chains", {})

    for chain, data in chains.items():
        for detector in (
            detect_accumulation,
            detect_distribution,
            detect_speculative_churn,
            detect_participation_shift,
        ):
            signal = detector(data)
            if signal and signal["confidence"] >= CONFIDENCE_FLOOR:
                signals.append(signal)

    for cross_detector in (detect_capital_rotation, detect_liquidity_migration):
        signal = cross_detector(chains)
        if signal and signal["confidence"] >= CONFIDENCE_FLOOR:
            signals.append(signal)

    return signals

# =========================================================
# CLI TEST
# =========================================================

if __name__ == "__main__":
    import json
    from backend.script_engine.onchain.chainstack_numeric_enricher import generate_numeric_enrichment

    numeric = generate_numeric_enrichment()
    print(json.dumps(generate_signals(numeric), indent=2))
