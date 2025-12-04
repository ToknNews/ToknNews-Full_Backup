#!/usr/bin/env python3
"""
enrich_v2.py
TokenNews 2025 — Unified Enrichment Engine

Takes a raw story:
{ "headline": "...", "source": "RSS" }

Outputs enriched object matching what PDv3 + timeline_builder_v3 require.
"""

import re
from openai import OpenAI
from backend.runtime.vault_loader import load_secrets

secrets = load_secrets()
OPENAI_API_KEY = secrets.get("openai_api_key", "")
client = OpenAI(api_key=OPENAI_API_KEY)


# -------------------------------------------------------
# DOMAIN DETECTION
# -------------------------------------------------------
DOMAIN_MAP = {
    "macro": ["fed", "inflation", "treasury", "rates", "yields"],
    "regulation": ["sec", "cftc", "lawsuit", "hearing", "regulator"],
    "markets": ["price", "btc", "eth", "market", "rally", "selloff", "volume"],
    "defi": ["defi", "liquidity", "staking", "aave", "uniswap"],
    "onchain": ["bridge", "exploit", "hack", "validator", "on-chain"],
    "ai": ["ai", "compute", "gpu", "nvidia", "model"],
    "culture": ["memecoin", "doge", "viral", "trend"],
    "general": []
}

def detect_domain(headline: str):
    h = headline.lower()
    for domain, words in DOMAIN_MAP.items():
        if any(w in h for w in words):
            return domain
    return "general"


# -------------------------------------------------------
# GPT SUMMARY
# -------------------------------------------------------
def summarize(headline: str):
    prompt = f"Summarize this in one sentence, no hype:\n{headline}"
    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            max_tokens=60,
            temperature=0.2
        )
        return rsp.choices[0].message.content.strip()
    except:
        return headline  # fallback


# -------------------------------------------------------
# SENTIMENT TAGGING
# -------------------------------------------------------
def get_sentiment(headline: str):
    if any(w in headline.lower() for w in ["surges","rises","jumps","growth"]):
        return "Positive"
    if any(w in headline.lower() for w in ["falls","drops","down","crash","tumbles"]):
        return "Negative"
    return "Neutral"


# -------------------------------------------------------
# ANCHOR SELECTION
# -------------------------------------------------------
ANCHORS = {
    "macro": ["bond"],
    "regulation": ["lawson"],
    "markets": ["cash","bond"],
    "defi": ["reef"],
    "onchain": ["ledger"],
    "ai": ["neura"],
    "culture": ["bitsy"],
    "general": ["chip"]
}

def choose_anchors(domain):
    return ANCHORS.get(domain, ["chip"])


# -------------------------------------------------------
# MAIN ENRICH FUNCTION
# -------------------------------------------------------
def enrich_item(raw):
    h = raw.get("headline","")
    domain = detect_domain(h)
    summary = summarize(h)
    sentiment = get_sentiment(h)
    anchors = choose_anchors(domain)

    enriched = {
        "headline": h,
        "summary": summary,
        "domain": domain,
        "sentiment": sentiment,
        "importance": 5,
        "anchors": anchors,
        "source": raw.get("source","RSS")
    }
    return enriched


# -------------------------------------------------------
# COMPAT WRAPPER (required by run_cycle.py)
# -------------------------------------------------------
def enrich_story(raw):
    return enrich_item(raw)

