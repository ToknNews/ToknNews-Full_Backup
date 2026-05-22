#!/usr/bin/env python3
"""
culture_ingest.py
ToknNews — Culture/Sentiment Synthetic Article Generator (v1)

Builds ONE persistent culture article per show from Reddit + X.
Runs ONLY when called by main ingestion.
"""

import os
import time
import json
import re
import logging
from datetime import datetime
from collections import Counter
from typing import List, Dict

import praw
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from backend.runtime.grok_client import call_grok

logger = logging.getLogger("culture_ingest")

# -----------------------------
# CONFIG
# -----------------------------

CULTURE_VERSION = "culture_ingest_v1"
WINDOW_HOURS = int(os.getenv("CULTURE_WINDOW_HOURS", "6"))
MIN_ENGAGEMENT = int(os.getenv("CULTURE_MIN_ENGAGEMENT", "50"))
MAX_QUOTES = 5

ENABLE_CULTURE_GROK = os.getenv("ENABLE_CULTURE_GROK", "false").lower() == "true"

TRACKED_SYMBOLS = [
    "BTC","ETH","SOL","WIF","BONK","MOG","PEPE","DOGE","SHIB","AVAX","BNB","ADA"
]

REDDIT_SUBS = [
    "cryptocurrency",
    "CryptoCurrency",
    "memecoins",
    "SatoshiStreetBets",
    "solana",
]

TOKEN_REGEX = re.compile(r"\$[A-Z]{2,6}")
analyzer = SentimentIntensityAnalyzer()

# -----------------------------
# REDDIT FETCH (POST-LEVEL)
# -----------------------------

def fetch_reddit_signals(window_start: int) -> List[Dict]:
    if not os.getenv("REDDIT_CLIENT_ID"):
        logger.warning("[CULTURE] Reddit credentials missing, skipping Reddit ingest")
        return []

    reddit = praw.Reddit(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
        user_agent=os.getenv("REDDIT_USER_AGENT", "ToknNews Culture Ingest"),
    )

    out = []
    for sub in REDDIT_SUBS:
        try:
            for post in reddit.subreddit(sub).hot(limit=50):
                if post.score < MIN_ENGAGEMENT:
                    continue
                if post.created_utc < window_start:
                    continue

                text = f"{post.title} {post.selftext}"
                sentiment = analyzer.polarity_scores(text)["compound"]
                symbols = TOKEN_REGEX.findall(text)

                out.append({
                    "platform": "reddit",
                    "author": f"u/{post.author}",
                    "text": text,
                    "sentiment": sentiment,
                    "symbols": symbols,
                    "engagement": post.score,
                    "created_at": int(post.created_utc),
                    "url": post.url,
                })
        except Exception as e:
            logger.warning(f"[CULTURE] Reddit fetch failed for r/{sub}: {e}")

    return out

# -----------------------------
# GROK X CULTURE (JSON ONLY)
# -----------------------------

def fetch_x_culture_json() -> Dict | None:
    if not ENABLE_CULTURE_GROK:
        return None

    grok_prompt = """
You are a data transformation engine for ToknNews.

TASK:
Analyze current crypto culture sentiment on X (Twitter).

STRICT OUTPUT RULES:
- Return VALID JSON only
- No markdown, prose, or commentary
- No backticks
- If a value cannot be determined, use null

REQUIRED JSON SCHEMA:
{
  "culture_summary": {
    "headline": "string",
    "summary": "string",
    "sentiment": "bullish | bearish | neutral | chaotic",
    "conviction": "low | medium | high",
    "themes": ["string"],
    "top_tokens": [{"symbol":"string","mentions":number}],
    "top_influencers": [{"handle":"string","stance":"bullish|bearish|neutral"}]
  },
  "evidence": {
    "x_sentiment_pct": {
      "bullish": number,
      "neutral": number,
      "bearish": number
    },
    "engagement_weighted_bias": number,
    "notable_quotes": [
      {
        "platform":"x",
        "author":"string",
        "quote":"string",
        "engagement":number
      }
    ]
  },
  "forward_outlook": {
    "base_case":"string",
    "risks":["string"],
    "watch_levels":["string"]
  }
}

Return the JSON now.
"""

    try:
        response = call_grok(
            prompt=grok_prompt,
            tools=["x_keyword_search"],
            max_tokens=400,
        )
        return json.loads(response)
    except Exception as e:
        logger.warning(f"[CULTURE] Grok JSON failed: {e}")
        return None

# -----------------------------
# BUILD CULTURE ARTICLE
# -----------------------------

def build_culture_article(last_run_ts: int | None = None) -> Dict:
    logger.info("[CULTURE] Culture ingest started")

    now = int(time.time())
    window_start = last_run_ts or (now - WINDOW_HOURS * 3600)

    reddit_posts = fetch_reddit_signals(window_start)
    grok_culture = fetch_x_culture_json()

    logger.info(
        f"[CULTURE] Signals collected — Reddit: {len(reddit_posts)} | GrokX: {'yes' if grok_culture else 'no'}"
    )

    if not reddit_posts and not grok_culture:
        return {
            "id": f"culture_{now}",
            "domain": "culture",
            "headline": "Crypto Culture Pulse: Quiet Session",
            "summary": "Crypto culture was quiet this session with no dominant narratives emerging.",
            "sentiment": "neutral",
            "importance": 3.0,
            "anchors": ["bitsy"],
            "source": CULTURE_VERSION,
            "timestamp": now,
            "market_data": {},
            "breaking": False,
            "signals": {},
            "evidence_quotes": [],
        }

    avg_sentiment = (
        sum(p["sentiment"] for p in reddit_posts) / len(reddit_posts)
        if reddit_posts else 0.0
    )

    sentiment_label = (
        "bullish" if avg_sentiment > 0.3 else
        "bearish" if avg_sentiment < -0.3 else
        "chaotic" if abs(avg_sentiment) >= 0.15 else
        "neutral"
    )

    evidence = sorted(
        reddit_posts,
        key=lambda p: abs(p["sentiment"]) * max(1, p["engagement"]),
        reverse=True
    )[:MAX_QUOTES]

    return {
        "id": f"culture_{now}",
        "domain": "culture",
        "headline": (
            grok_culture["culture_summary"]["headline"]
            if grok_culture else f"Crypto Culture Pulse: {sentiment_label.title()}"
        ),
        "summary": (
            grok_culture["culture_summary"]["summary"]
            if grok_culture else
            f"Crypto culture turned {sentiment_label} over the last {WINDOW_HOURS} hours."
        ),
        "sentiment": (
            grok_culture["culture_summary"]["sentiment"]
            if grok_culture else sentiment_label
        ),
        "importance": min(10.0, 5 + abs(avg_sentiment) * 5 + len(reddit_posts) / 20),
        "anchors": ["bitsy"],
        "source": CULTURE_VERSION,
        "timestamp": now,
        "market_data": {},
        "breaking": False,

        "signals": {
            "reddit_posts": len(reddit_posts),
            "avg_sentiment": round(avg_sentiment, 2),
            "grok_culture": grok_culture,
        },

        "evidence_quotes": [
            {
                "platform": p["platform"],
                "author": p["author"],
                "quote": p["text"][:180],
                "engagement": p["engagement"],
            } for p in evidence
        ],
    }
