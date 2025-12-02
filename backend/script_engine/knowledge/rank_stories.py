#!/usr/bin/env python3
"""
TOKNNews — Story Ranking Engine (Editorial Layer)
Ranks raw enriched stories into a production-ready stack.
"""

import time

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

SENTIMENT_WEIGHTS = {
    "Positive": 3,
    "Negative": 5,
    "Neutral": 1
}

def score_story(story):
    now = time.time()
    hours_old = (now - story.get("timestamp", now - 3600)) / 3600
    recency = max(0, min(10, 10 - hours_old))

    domain = story.get("domain", "general").lower()
    sent = story.get("sentiment", "Neutral").capitalize()
    importance_score = float(story.get("importance", 1)) * 2.0

    domain_score = DOMAIN_WEIGHTS.get(domain, 2)
    sentiment_score = SENTIMENT_WEIGHTS.get(sent, 1)

    if domain == "breaking" and hours_old < 2:
        domain_score += 3

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
        s2 = dict(s)
        s2["rank_score"] = score_story(s)
        ranked.append(s2)

    ranked.sort(key=lambda x: x["rank_score"], reverse=True)
    return ranked
