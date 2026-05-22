#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS ENTITY RESOLVER

Purpose
-------
Resolves raw entities (contracts, tickers, noise) into
broadcast-safe labels.

• prevents contract spam
• prepares inputs for anchors
• enables Bitsy meme routing
"""

from typing import Dict

KNOWN_MAP: Dict[str, str] = {
    "BTC": "Bitcoin",
    "ETH": "Ethereum",
    "SOL": "Solana",
    "USDT": "Tether",
    "USDC": "USD Coin",
    "SP500": "S&P 500",
    "VIXCLS": "VIX",
}


def is_contract(entity: str) -> bool:
    return len(entity) > 20


def resolve_entity(entity: str) -> str:
    if not entity:
        return ""

    e = entity.strip()

    if e.upper() in KNOWN_MAP:
        return KNOWN_MAP[e.upper()]

    if is_contract(e):
        return f"token {e[:6]}..."

    return e


def classify_entity(entity: str) -> str:
    e = entity.upper()

    if e in ["BTC", "ETH", "SOL"]:
        return "major"

    if "PUMP" in e:
        return "memecoin"

    if is_contract(e):
        return "contract"

    return "general"
