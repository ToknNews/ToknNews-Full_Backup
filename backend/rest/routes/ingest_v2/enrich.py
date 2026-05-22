#!/usr/bin/env python3
"""
enrich.py  
TOKEN NEWS — Story Enrichment (2025 Rebuild)

This module:
 - Normalizes raw RSS/API items
 - Performs Hybrid Domain Classification:
      1) Keyword classifier
      2) GPT fallback (gpt-4o-mini)
 - Scores sentiment + volatility
 - Computes story importance
 - Suggests appropriate anchors based on domain
 - Produces PD-ready story objects
"""

import os
import time
import re
import openai
from backend.runtime.vault_loader import load_secrets
secrets = load_secrets()

openai.api_key = os.getenv("OPENAI_API_KEY")

# Import PD domain → anchor mapping
from backend.script_engine.director.pd_controller import get_domain_anchors


# ============================================================
# 1. NORMALIZATION
# ============================================================

def normalize_item(raw):
    """Convert raw RSS/API item into standardized structure."""
    return {
        "headline": raw.get("title") or raw.get("headline") or "",
        "summary": raw.get("summary") or raw.get("description") or "",
        "source": raw.get("source", "unknown"),
        "url": raw.get("url") or raw.get("link"),
        "timestamp": _extract_timestamp(raw),
        "raw": raw,  # keep entire raw payload for debugging
    }


def _extract_timestamp(raw):
    """Extract timestamp or fallback to now."""
    ts = raw.get("published_at") or raw.get("pubDate") or raw.get("published") or raw.get("timestamp")
    try:
        return float(ts)
    except:
        return time.time()


# ============================================================
# 2. KEYWORD DOMAIN CLASSIFIER
# ============================================================

DOMAIN_KEYWORDS = {
    "macro":      ["inflation", "cpi", "rates", "fed", "treasury", "macro", "interest"],
    "markets":    ["market", "price", "stock", "equity", "btc", "eth", "crypto", "token"],
    "regulation": ["sec", "lawsuit", "regulator", "court", "bill", "congress", "policy"],
    "defi":       ["defi", "liquidity", "pool", "dex", "amm", "yield", "staking"],
    "onchain":    ["hacked", "exploit", "bridge", "validator", "onchain", "smart contract"],
    "ai":         ["ai", "compute", "gpu", "model", "llm"],
    "venture":    ["funding", "raised", "seed", "series", "venture", "vc"],
    "retail":     ["consumer", "retail", "wallet", "adoption", "shoppers", "mainstream"],
    "sentiment":  ["sentiment", "fomo", "panic", "viral", "trend", "memecoin"],
    "meta":       ["crypto twitter", "meme", "community meltdown", "timeline"],
}


def keyword_domain(headline, summary):
    text = (headline + " " + summary).lower()
    for domain, words in DOMAIN_KEYWORDS.items():
        if any(w in text for w in words):
            return domain
    return None


# ============================================================
# 3. GPT FALLBACK DOMAIN CLASSIFIER
# ============================================================

def gpt_classify_domain(headline, summary):
    prompt = f"""
Classify this crypto/finance story into EXACTLY one domain:

Domains:
macro, markets, regulation, defi, onchain, ai, venture,
retail, sentiment, meta, general

Headline: {headline}
Summary: {summary}

Respond with the one domain word ONLY.
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=5
        )
        return resp.choices[0].message.content.strip().lower()
    except:
        return "general"


# ============================================================
# 4. SENTIMENT SCORING
# ============================================================

POSITIVE_WORDS = [
    "surge", "gain", "record", "rise", "upgrade",
    "partner", "launch", "milestone"
]

NEGATIVE_WORDS = [
    "crash", "fear", "lawsuit", "ban", "exploit", "hack",
    "collapse", "down", "scandal"
]

def score_sentiment(h, s):
    text = (h + " " + s).lower()
    score = 0
    for w in POSITIVE_WORDS:
        if w in text:
            score += 1
    for w in NEGATIVE_WORDS:
        if w in text:
            score -= 1

    if score > 0:  return "positive"
    if score < 0:  return "negative"
    return "neutral"


# ============================================================
# 5. VOLATILITY DETECTION
# ============================================================

VOLATILITY_WORDS = [
    "spike", "surge", "collapse", "flash", "liquidation",
    "cascade", "panic"
]

def score_volatility(h, s):
    text = (h + " " + s).lower()
    return sum(w in text for w in VOLATILITY_WORDS)


# ============================================================
# 6. IMPORTANCE MODEL
# ============================================================

def compute_importance(sentiment, volatility, domain):
    base = 5
    if volatility > 1:
        base += 1
    if sentiment == "negative":
        base += 1
    if domain in ["macro", "markets", "regulation", "defi"]:
        base += 1
    return min(base, 10)


# ============================================================
# 7. ANCHOR SUGGESTION (domain → anchor)
# ============================================================

def suggest_anchors(domain):
    anchors = get_domain_anchors(domain)
    return anchors[:2]  # allow duo


# ============================================================
# 8. MASTER ENRICH FUNCTION
# ============================================================

def enrich(raw_item):
    """
    Convert raw feed/API data into a fully enriched story ready
    for ranking, PD-controller, and timeline_builder.
    """

    item = normalize_item(raw_item)
    h = item["headline"]
    s = item["summary"]

    # Domain
    domain = keyword_domain(h, s)
    if not domain:
        domain = gpt_classify_domain(h, s)

    # === Phase 3B Crypto-First Domain Rebalancing ===
    from script_engine.knowledge.domain_rebalance import rebalance_domain

    domain = rebalance_domain(
        headline=h,
        summary=s,
        original_domain=domain
    )

    # Sentiment + Volatility
    sentiment  = score_sentiment(h, s)
    volatility = score_volatility(h, s)

    # Importance
    importance = compute_importance(sentiment, volatility, domain)

    # Anchors
    anchors = suggest_anchors(domain)

    item.update({
        "domain": domain,
        "sentiment": sentiment,
        "volatility": volatility,
        "importance": importance,
        "anchors": anchors
    })

    return item
