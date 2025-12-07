#!/usr/bin/env python3
"""
enrich_v2.py
ToknNews 2025 — Canonical Enrichment Engine (Transfer Brain v1.0)

Summary:
 - GPT-first one-sentence summary (neutral)
 - Domain classification
 - Sentiment tagging
 - Anchor mapping
 - Importance default = 5
"""

import time
import re
from openai import OpenAI
from backend.runtime.vault_loader import load_secrets

# ---------------------------------------------------------------
# OpenAI client (GPT-first design)
# ---------------------------------------------------------------

_secrets = load_secrets()
OPENAI_API_KEY = _secrets.get("openai_api_key", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ---------------------------------------------------------------
# DOMAIN MAP
# ---------------------------------------------------------------

DOMAIN_MAP = {
    "macro":      ["fed", "inflation", "treasury", "rates", "yields"],
    "regulation": ["sec", "cftc", "lawsuit", "hearing", "regulator"],
    "markets":    ["btc", "eth", "price", "market", "rally", "selloff", "volume"],
    "defi":       ["defi", "staking", "liquidity", "aave", "uniswap"],
    "onchain":    ["onchain", "bridge", "exploit", "hack", "validator"],
    "ai":         ["ai", "compute", "gpu", "nvidia", "model"],
    "culture":    ["memecoin", "viral", "trend", "doge", "community"],
    "general":    [],
}


def detect_domain(headline: str) -> str:
    h = headline.lower()
    for domain, words in DOMAIN_MAP.items():
        if any(w in h for w in words):
            return domain
    return "general"


# ---------------------------------------------------------------
# GPT-FIRST SUMMARY FUNCTION
# (20s timeout, fallback only on error)
# ---------------------------------------------------------------

def summarize(headline: str) -> str:
    """
    GPT-first summarizer.
    Timeout = 20 seconds.
    Fallback only on failure.
    """
    fallback = f"A brief update regarding {headline.lower()}.".capitalize()

    if client is None:
        return fallback

    prompt = (
        "Summarize this crypto headline in ONE neutral sentence. "
        "No hype, no predictions, no adjectives:\n"
        f"{headline}"
    )

    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=45,
            temperature=0.1,
            timeout=20
        )
        text = rsp.choices[0].message.content.strip()

        # enforce one sentence
        if "." in text:
            return text.split(".", 1)[0].strip() + "."
        return text + "."

    except Exception:
        return fallback


# ---------------------------------------------------------------
# SENTIMENT
# ---------------------------------------------------------------

POS_WORDS = ["surges", "rises", "jumps", "soars", "growth", "up"]
NEG_WORDS = ["falls", "drops", "down", "crash", "tumbles", "decline"]


def get_sentiment(headline: str) -> str:
    h = headline.lower()
    if any(w in h for w in POS_WORDS):
        return "Positive"
    if any(w in h for w in NEG_WORDS):
        return "Negative"
    return "Neutral"


# ---------------------------------------------------------------
# ANCHOR MAP
# ---------------------------------------------------------------

ANCHORS = {
    "macro":      ["bond"],
    "regulation": ["lawson"],
    "markets":    ["cash","bond"],
    "defi":       ["reef"],
    "onchain":    ["ledger"],
    "ai":         ["neura"],
    "culture":    ["bitsy"],
    "general":    ["chip"],
}


def choose_anchors(domain: str):
    return ANCHORS.get(domain, ["chip"])


# ---------------------------------------------------------------
# MAIN ENRICH LOGIC
# ---------------------------------------------------------------

def enrich_item(raw):
    headline = raw.get("headline", "").strip()
    ts = raw.get("timestamp", time.time())

    domain = detect_domain(headline)
    summary = summarize(headline)
    sentiment = get_sentiment(headline)
    anchors = choose_anchors(domain)

    enriched = {
        "headline": headline,
        "summary": summary,
        "domain": domain,
        "sentiment": sentiment,
        "importance": 5,
        "anchors": anchors,
        "source": raw.get("source", "RSS"),
        "timestamp": ts
    }

    return enriched


def enrich_story(raw):
    return enrich_item(raw)


if __name__ == "__main__":
    test = {
        "headline": "Bitcoin surges as ETF flows accelerate",
        "source": "API",
        "timestamp": time.time()
    }
    print(enrich_item(test))
