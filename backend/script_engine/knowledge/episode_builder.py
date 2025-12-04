#!/usr/bin/env python3
"""
TOKNNews — Episode Builder (2025 GPT-Enriched Edition)

This module:
 • Loads rolling_stories.json
 • Cleans + enriches every story
 • Runs GPT-4o summarizer when summary is empty
 • Detects domain (macro/defi/markets/etc.)
 • Computes sentiment
 • Selects correct anchors for timeline_builder
 • Outputs perfect PD-ready story clusters
"""

import json
import os
import time
from loguru import logger
from openai import OpenAI

# GPT client (Vault handled upstream)
from backend.runtime.vault_loader import load_secrets
OPENAI_API_KEY = load_secrets().get("openai_api_key", "")
client = OpenAI(api_key=OPENAI_API_KEY)

ROLLING_PATH = "/var/www/toknnews-live/data/rolling_stories.json"
EPISODE_OUTPUT = "/opt/toknnews/data/episodes"


# -------------------------------------------------------------
# DOMAIN KEYWORDS (simple + effective)
# -------------------------------------------------------------
DOMAIN_KEYWORDS = {
    "macro":      ["fed", "inflation", "treasury", "cpi", "yield", "rate", "fomc"],
    "markets":    ["price", "trading", "etf", "volume", "selloff", "rally"],
    "defi":       ["defi", "uniswap", "lending", "staking", "amm", "yield"],
    "onchain":    ["on-chain", "onchain", "wallet", "bridge", "layer 2", "l2"],
    "regulation": ["sec", "lawsuit", "policy", "court", "legal", "cftc"],
    "ai":         ["ai", "model", "compute", "machine learning"],
    "venture":    ["funding", "investor", "venture", "raise"],
    "culture":    ["memecoin", "meme", "culture", "trend"],
    "retail":     ["retail", "consumer", "adoption", "shopping"],
}


def detect_domain(headline: str) -> str:
    h = (headline or "").lower()
    scores = {d: sum(1 for w in words if w in h) for d, words in DOMAIN_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "markets"


# -------------------------------------------------------------
# Sentiment Classifier (GPT-4o)
# -------------------------------------------------------------
def classify_sentiment(text: str) -> str:
    if not text:
        return "neutral"
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Classify sentiment as positive, neutral, or negative."},
                {"role": "user", "content": text},
            ],
            max_tokens=6,
        )
        raw = resp.choices[0].message.content.strip().lower()
        if "pos" in raw: return "positive"
        if "neg" in raw: return "negative"
    except:
        pass
    return "neutral"


# -------------------------------------------------------------
# GPT-4o Summarizer
# -------------------------------------------------------------
def gpt_summarize(headline: str, body: str = "") -> str:
    prompt = f"""
Summarize this crypto/finance story in one sentence, crisp and factual:

Headline: {headline}
Body: {body[:2000]}
"""

    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.3,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        logger.error(f"[EpisodeBuilder] Summarizer error: {e}")
        return headline  # fallback


# -------------------------------------------------------------
# Anchor Router
# -------------------------------------------------------------
ANCHOR_MAP = {
    "macro":      ["bond", "ledger", "chip"],
    "markets":    ["cash", "bond", "reef"],
    "regulation": ["lawson", "bond"],
    "defi":       ["reef", "ledger"],
    "onchain":    ["ledger", "reef"],
    "ai":         ["neura", "chip"],
    "venture":    ["cap", "chip"],
    "retail":     ["penny", "cash"],
    "culture":    ["bitsy", "chip"],
    "sentiment":  ["ivy", "cash"],
    "general":    ["chip"],
}

HIGH_HEAT = {"macro", "markets", "regulation", "defi", "onchain", "ai"}


def choose_anchors(domain: str):
    anchors = ANCHOR_MAP.get(domain, ["chip"])
    # high-heat → ensure two anchors minimum
    if domain in HIGH_HEAT and len(anchors) < 2:
        anchors.append("chip")
    return anchors[:2]


# -------------------------------------------------------------
# Episode Builder MAIN
# -------------------------------------------------------------
def load_rolling():
    try:
        with open(ROLLING_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"[EpisodeBuilder] Failed to load rolling stories: {e}")
        return []


def build_episode(rundown_count=6):
    raw = load_rolling()
    if not raw:
        return {"error": "no stories available"}

    # ranked stories
    from script_engine.knowledge.rank_stories import rank_stories
    ranked = rank_stories(raw)
    rundown = ranked[:rundown_count]

    enriched = []
    for s in rundown:
        headline = s.get("headline", "")
        body     = s.get("body", "")
        domain   = detect_domain(headline)
        summary  = s.get("summary") or gpt_summarize(headline, body)
        sentiment = classify_sentiment(headline + " " + body)

        enriched.append({
            "headline":   headline,
            "summary":    summary,
            "body":       body,
            "domain":     domain,
            "sentiment":  sentiment,
            "importance": s.get("importance", 5),
            "rank_score": s.get("rank_score", 0),
            "anchors":    choose_anchors(domain),
        })

    episode_id = f"episode_{int(time.time())}"
    episode = {
        "timestamp": time.time(),
        "episode_id": episode_id,
        "rundown": enriched,
    }

    # save to disk
    os.makedirs(EPISODE_OUTPUT, exist_ok=True)
    out_path = f"{EPISODE_OUTPUT}/{episode_id}.json"
    with open(out_path, "w") as f:
        json.dump(episode, f, indent=2)

    logger.info(f"[EpisodeBuilder] Episode saved → {out_path}")
    return episode
