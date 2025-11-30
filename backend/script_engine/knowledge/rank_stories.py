#!/usr/bin/env python3
"""
TOKNNews — Story Ranking Engine (Editorial Layer)
Ranks raw enriched stories into a production-ready stack.

Inputs:
 - list of enriched story dicts (headline, summary, importance, sentiment, domain, ts)
Outputs:
 - sorted list with attached `rank_score`
"""

import time

# Domain priorities (Chip + PD combined weighting)
DOMAIN_WEIGHTS = {
    "breaking": 12,
    "macro": 10,
    "markets": 9,
    "legal": 8,
    "defi": 7,
    "onchain": 7,
    "ai": 6,
    "venture": 5,
    "sentiment": 4,
    "culture": 3,
    "retail": 3,
    "general": 2
}

# Sentiment weighting
SENTIMENT_WEIGHTS = {
    "Positive": 3,
    "Negative": 5,
    "Neutral": 1
}


def score_story(story):
    now = time.time()

    # Recency score (0–10)
    hours_old = (now - story.get("timestamp", now - 3600)) / 3600  # fallback to 1h old
    recency = max(0, 10 - hours_old)

    # Domain score
    domain = story.get("domain", "general")
    domain_score = DOMAIN_WEIGHTS.get(domain.lower(), 2)

    # Sentiment volatility score
    sent = story.get("sentiment", "Neutral")
    sentiment_score = SENTIMENT_WEIGHTS.get(sent, 1)

    # Importance
    importance_score = story.get("importance", 1) * 2.5

    # Final weighted score
    rank_score = (
        importance_score +
        recency * 1.5 +
        domain_score * 2 +
        sentiment_score
    )

    return rank_score


def rank_stories(stories):
    ranked = []
    for s in stories:
        s2 = dict(s)  # copy to avoid mutating
        s2["rank_score"] = score_story(s)
        ranked.append(s2)

    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    return ranked
