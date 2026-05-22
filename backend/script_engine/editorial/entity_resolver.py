#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS ENTITY RESOLVER
---------------------------------------

Purpose
-------
Resolves raw entity identifiers into broadcast-safe display names.

This module:
• Converts contract addresses into readable labels
• Detects memecoin / pump.fun style entities
• Prevents anchors from speaking raw hashes on air
• Supports downstream persona + TTS clarity

Primary Input
-------------
- entity (string)
- title (optional)
- summary (optional)

Primary Output
--------------
{
  "display": "Readable Name",
  "type": "named | contract | meme_contract | alpha_contract"
}

Design Notes
------------
• Deterministic (NO LLM usage)
• Fast and safe for real-time pipeline
• Extensible for future token metadata resolution
• Designed for anchor readability + TTS clarity

Author: TOKN Systems
"""

import re


def resolve_entity(entity: str, title: str = "", summary: str = "") -> dict:
    """
    Resolve entity into a display-safe format.
    """

    if not entity:
        return {"display": "", "type": "unknown"}

    e = entity.strip()

    # Detect contract-like strings
    is_contract = bool(re.match(r"^[A-Za-z0-9]{30,}$", e))

    if not is_contract:
        return {"display": e, "type": "named"}

    lower_title = (title or "").lower()
    lower_summary = (summary or "").lower()

    # --- MEME DETECTION ---
    if "pump.fun" in lower_title or "pump.fun" in lower_summary:
        return {"display": "Pump.fun Token", "type": "meme_contract"}

    if "memecoin" in lower_title:
        return {"display": "Trending Memecoin", "type": "meme_contract"}

    # --- ALPHA / SOLANA SIGNALS ---
    if "alpha" in lower_title:
        return {"display": "Solana Alpha Token", "type": "alpha_contract"}

    # --- DEFAULT CONTRACT FALLBACK ---
    return {"display": f"Token {e[:4]}…{e[-4:]}", "type": "contract"}
