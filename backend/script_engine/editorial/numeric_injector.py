#!/usr/bin/env python3
"""
numeric_injector.py
ToknNews — Numeric Context Extractor for Dialogue

Builds compact, spoken-friendly numeric talking points from:
- market_data
- ToknClaw metrics
- ToknClaw deltas
- ToknClaw memory
- signal_data
"""

from __future__ import annotations
from typing import Any, Dict, List


def _fmt_money(value: float | int | None) -> str:
    if value is None:
        return ""
    try:
        value = float(value)
    except Exception:
        return ""
    if value >= 1_000_000_000:
        return f"${value / 1_000_000_000:.1f}B"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"${value / 1_000:.0f}K"
    return f"${value:,.0f}"


def _safe_float(x: Any) -> float | None:
    try:
        if x is None:
            return None
        return float(x)
    except Exception:
        return None


def build_numeric_context(brief: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Returns a list of broadcast-ready numeric cues.
    Each item:
    {
        "type": "...",
        "label": "...",
        "spoken": "...",
        "value": "...",
        "priority": int
    }
    """
    out: List[Dict[str, Any]] = []

    context = brief.get("context") or {}
    market_data = context.get("market_data") or brief.get("market_data") or {}
    tokn = context.get("toknclaw_context") or brief.get("toknclaw_context") or {}

    # --------------------------------------------------
    # 1. Price / market data
    # --------------------------------------------------
    price_block = market_data.get("price") if isinstance(market_data, dict) else None
    if isinstance(price_block, dict):
        symbol = price_block.get("symbol")
        price_usd = _safe_float(price_block.get("price_usd"))
        change_24h = _safe_float(price_block.get("change_24h_pct"))

        if symbol and price_usd is not None and change_24h is not None:
            direction = "up" if change_24h >= 0 else "down"
            out.append({
                "type": "price",
                "label": f"{symbol}_price",
                "spoken": f"{symbol} is {direction} about {abs(change_24h):.1f} percent at roughly ${price_usd:,.2f}",
                "value": f"{change_24h:+.2f}%",
                "priority": 8
            })

    # --------------------------------------------------
    # 2. ToknClaw metrics
    # --------------------------------------------------
    metrics = tokn.get("metrics") if isinstance(tokn, dict) else {}
    if isinstance(metrics, dict):
        whale_usd = _safe_float(metrics.get("whale_activity_usd"))
        inflows_usd = _safe_float(metrics.get("exchange_inflows_usd"))
        outflows_usd = _safe_float(metrics.get("exchange_outflows_usd"))
        liq_usd = _safe_float(metrics.get("defi_liquidations_usd"))

        if whale_usd and whale_usd > 0:
            out.append({
                "type": "metric",
                "label": "whale_activity",
                "spoken": f"whale activity totaled about {_fmt_money(whale_usd)} this cycle",
                "value": _fmt_money(whale_usd),
                "priority": 10
            })

        if inflows_usd and inflows_usd > 0:
            out.append({
                "type": "metric",
                "label": "exchange_inflows",
                "spoken": f"exchange inflows came in around {_fmt_money(inflows_usd)}",
                "value": _fmt_money(inflows_usd),
                "priority": 10
            })

        if outflows_usd and outflows_usd > 0:
            out.append({
                "type": "metric",
                "label": "exchange_outflows",
                "spoken": f"exchange outflows were about {_fmt_money(outflows_usd)}",
                "value": _fmt_money(outflows_usd),
                "priority": 9
            })

        if liq_usd and liq_usd > 0:
            out.append({
                "type": "metric",
                "label": "defi_liquidations",
                "spoken": f"DeFi liquidations reached roughly {_fmt_money(liq_usd)}",
                "value": _fmt_money(liq_usd),
                "priority": 10
            })

    # --------------------------------------------------
    # 3. ToknClaw deltas
    # --------------------------------------------------
    deltas = tokn.get("deltas") if isinstance(tokn, dict) else {}
    if isinstance(deltas, dict):
        inflow_delta = (deltas.get("exchange_inflows_usd") or {})
        liq_delta = (deltas.get("defi_liquidations_usd") or {})
        whale_delta = (deltas.get("whale_activity_usd") or {})

        for label, block in (
            ("exchange inflows", inflow_delta),
            ("liquidations", liq_delta),
            ("whale activity", whale_delta),
        ):
            if not isinstance(block, dict):
                continue

            absolute_change = _safe_float(block.get("absolute_change"))
            percent_change = _safe_float(block.get("percent_change"))

            if absolute_change is None and percent_change is None:
                continue

            if percent_change is not None:
                direction = "up" if percent_change >= 0 else "down"
                out.append({
                    "type": "delta",
                    "label": f"{label}_delta",
                    "spoken": f"{label} are {direction} about {abs(percent_change):.1f} percent versus the previous cycle",
                    "value": f"{percent_change:+.1f}%",
                    "priority": 9
                })
            elif absolute_change is not None:
                direction = "up" if absolute_change >= 0 else "down"
                out.append({
                    "type": "delta",
                    "label": f"{label}_delta",
                    "spoken": f"{label} are {direction} versus the previous cycle",
                    "value": direction,
                    "priority": 7
                })

    # --------------------------------------------------
    # 4. ToknClaw memory
    # --------------------------------------------------
    memory = tokn.get("memory") if isinstance(tokn, dict) else {}
    if isinstance(memory, dict):
        exchange_flow_trend = memory.get("exchange_flow_trend")
        exchange_flow_cycles = memory.get("exchange_flow_cycles")
        whale_trend = memory.get("whale_activity_trend")
        liq_trend = memory.get("liquidation_trend")

        if exchange_flow_trend == "rising" and exchange_flow_cycles:
            out.append({
                "type": "memory",
                "label": "exchange_flow_trend",
                "spoken": f"exchange flows have been rising for {exchange_flow_cycles} cycles",
                "value": str(exchange_flow_cycles),
                "priority": 9
            })

        if whale_trend == "rising":
            out.append({
                "type": "memory",
                "label": "whale_trend",
                "spoken": "whale activity has been rising across recent cycles",
                "value": "rising",
                "priority": 8
            })

        if liq_trend == "rising":
            out.append({
                "type": "memory",
                "label": "liquidation_trend",
                "spoken": "liquidation pressure has been building across recent cycles",
                "value": "rising",
                "priority": 9
            })

    # --------------------------------------------------
    # 5. Individual signal data from context signals
    # --------------------------------------------------
    signal_context = brief.get("pd_hints", {}).get("signal_context") or []
    if isinstance(signal_context, list):
        for sig in signal_context[:3]:
            if not isinstance(sig, dict):
                continue

            entity = sig.get("entity")
            signal_type = sig.get("signal_type")
            value_usd = _safe_float(sig.get("value_usd"))

            if entity and signal_type and value_usd and value_usd > 0:
                out.append({
                    "type": "signal",
                    "label": f"{entity}_{signal_type}",
                    "spoken": f"{entity} saw a {signal_type.replace('_', ' ')} worth about {_fmt_money(value_usd)}",
                    "value": _fmt_money(value_usd),
                    "priority": 8
                })

    # highest-value facts first
    out.sort(key=lambda x: x.get("priority", 0), reverse=True)

    # keep prompt compact
    return out[:6]
