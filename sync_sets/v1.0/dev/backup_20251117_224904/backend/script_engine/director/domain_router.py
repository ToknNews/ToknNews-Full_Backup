#!/usr/bin/env python3
"""
TOKNNews — Domain Router
Maps a headline → topic domain → selects correct anchors.
Uses Character Bible for domain weights.
"""

import re
from script_engine.character_brain.persona_loader import get_bible

# ---------------------------------------------------------
# DOMAIN KEYWORD MAP
# ---------------------------------------------------------
DOMAIN_KEYWORDS = {
    "regulation": ["sec", "lawsuit", "cftc", "regulation", "policy", "congress", "hearing", "legal"],
    "markets": ["pump", "dump", "price", "etf", "volume", "liquidations", "funding", "market"],
    "defi": ["defi", "liquidity pool", "yield", "staking", "amm", "uniswap", "lending"],
    "tech": ["upgrade", "mainnet", "layer 2", "zk", "bridge", "hackfix", "node", "protocol"],
    "security": ["hack", "exploit", "breach", "phishing", "attack"],
    "memes": ["memecoin", "doge", "shiba", "viral", "trend", "culture"],
    "macro": ["inflation", "jobs report", "fomc", "macro", "dollar", "treasury"],
}

# ---------------------------------------------------------
# DETECT DOMAIN
# ---------------------------------------------------------
def detect_domain(headline: str):
    h = headline.lower()
    scores = {}

    for domain, words in DOMAIN_KEYWORDS.items():
        scores[domain] = sum(1 for w in words if w in h)

    # Pick highest scoring domain or fallback "markets"
    best = max(scores, key=scores.get)
    if scores[best] == 0:
        return "markets"

    return best

# ---------------------------------------------------------
# SCORE ANCHORS BASED ON CHARACTER BIBLE
# ---------------------------------------------------------
def score_anchors(domain: str):
    scores = {}
    for character, info in get_bible("").items():
        # get_bible("") returns nothing — so we iterate manually
        pass

    # Bible is loaded as a dict:
    bible = get_bible("__all__") or None
    # If "__all__" isn't used, fallback:
    if bible is None:
        bible = {}

    # But typically Bible is keyed like: bible["chip"], bible["lawson"], etc.
    bible = get_bible  # shorthand

    candidates = ["chip", "lawson", "reef", "bond", "vega", "bitsy", "neura", "ivy", "penny", "rex", "cap"]

    for c in candidates:
        entry = bible(c) or {}
        domains = entry.get("domain", {})
        weight = domains.get(domain, 0)
        scores[c] = weight

    # Sort descending
    sorted_chars = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return sorted_chars

# ---------------------------------------------------------
# PUBLIC API — SELECT ANCHORS FOR THIS HEADLINE
# ---------------------------------------------------------
def select_anchors_for_headline(headline: str, max_count=2):
    domain = detect_domain(headline)
    ranked = score_anchors(domain)

    # Keep only those with weight > 0
    top = [c for c, w in ranked if w > 0]

    if not top:
        # fallback to Chip + Lawson
        return ["lawson"]

    return top[:max_count]
