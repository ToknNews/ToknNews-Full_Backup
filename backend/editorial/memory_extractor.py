#!/usr/bin/env python3
"""
memory_extractor.py — Editorial Engine v4

Extracts:
  • Entities (projects, tokens, people)
  • Chains
  • Firms (VC, market makers, exchanges)
  • Behavioral patterns (e.g. “risk-off rotation”)
  • Flags for long-term narrative arcs

Output:
{
   "entities": [...],
   "chains": [...],
   "firms": [...],
   "patterns": [...],
   "arc_flags": {...}    # signals long-term arcs
}
"""

import re
from typing import Dict, List


# ------------------------------------------------------------
# Dictionaries / vocab
# ------------------------------------------------------------

TOKEN_REGEX = r"\b[A-Z]{2,5}\b"     # captures BTC, ETH, SOL, AAVE, etc.

CHAIN_KEYWORDS = {
    "ethereum": ["ethereum", "eth", "l2", "rollup"],
    "solana":   ["solana", "sol", "validator", "saga"],
    "bitcoin":  ["bitcoin", "btc", "halving", "ordinals"],
    "cosmos":   ["cosmos", "atom", "ibc"],
}

FIRM_PATTERNS = [
    "coinbase", "binance", "kraken", "okx",
    "blackrock", "fidelity", "tesla", "vanEck",
    "jump", "citadel", "paradigm", "a16z", "multicoin",
]

PATTERN_RULES = {
    "risk_off":    ["selloff", "liquidation", "rate hike", "fear"],
    "risk_on":     ["rally", "risk-on", "bullish", "rotation"],
    "regulatory":  ["sec", "hearing", "lawsuit", "compliance", "cftc"],
    "ai_infusion": ["ai", "gpu", "compute", "inference", "training"],
}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _find_tokens(text: str) -> List[str]:
    """Return all symbol-like uppercase tokens (BTC, ETH, etc.)."""
    return re.findall(TOKEN_REGEX, text)


def _match_keywords(text: str, table: Dict[str, List[str]]) -> List[str]:
    """Return keys whose keyword list appears in the text."""
    found = []
    for key, kws in table.items():
        for k in kws:
            if k in text:
                found.append(key)
                break
    return found


def _match_firms(text: str) -> List[str]:
    return [f for f in FIRM_PATTERNS if f in text]


def _match_patterns(text: str) -> List[str]:
    out = []
    for name, kws in PATTERN_RULES.items():
        for k in kws:
            if k in text:
                out.append(name)
                break
    return out


# ------------------------------------------------------------
# ARC FLAGS
# ------------------------------------------------------------

def _arc_flags(patterns: List[str]) -> Dict[str, bool]:
    """
    Flags that editorial engine + PD can turn into long-term arcs.
    """
    return {
        "macro_stress":    ("risk_off" in patterns),
        "bull_rotation":   ("risk_on" in patterns),
        "reg_pressure":    ("regulatory" in patterns),
        "ai_shift":        ("ai_infusion" in patterns),
    }


# ------------------------------------------------------------
# MAIN EXTRACTOR
# ------------------------------------------------------------

def extract_memory(story: Dict) -> Dict:
    """
    Takes normalized story:
      { headline, body, ... }
    Returns editorial memory features.
    """
    text = f"{story.get('headline', '')} {story.get('body', '')}".lower()

    tokens   = _find_tokens(text)
    chains   = _match_keywords(text, CHAIN_KEYWORDS)
    firms    = _match_firms(text)
    patterns = _match_patterns(text)
    arcs     = _arc_flags(patterns)

    return {
        "entities": tokens,
        "chains": chains,
        "firms": firms,
        "patterns": patterns,
        "arc_flags": arcs,
    }


# ------------------------------------------------------------
# Demo
# ------------------------------------------------------------
if __name__ == "__main__":
    sample = {
        "headline": "ETH liquidations spike as Binance whales rotate to SOL",
        "body": "Markets show risk-off behavior while Ethereum gas rises."
    }
    print("\n=== MEMORY EXTRACTION ===")
    print(extract_memory(sample))
