#!/usr/bin/env python3
"""
ToknNews Topic Clusterer (v1)

Groups recent enriched stories into small clusters based on:
 - domain
 - sentiment
 - keyword overlap (very light)
Later: replace with OpenAI-driven clustering logic.
"""

from collections import defaultdict


def cluster_articles(articles):
    """
    articles: list[dict] enriched items from ingest.
    Returns:
        list of clusters, where each cluster is a list of article dicts
    """
    if not articles:
        return []

    clusters = defaultdict(list)

    for a in articles:
        domain = a.get("domain", "general").lower()
        sentiment = a.get("sentiment", "neutral").lower()

        # Cheap keyword extraction
        headline = (a.get("headline") or "").lower()
        if "bitcoin" in headline or "btc" in headline:
            topic = "bitcoin"
        elif "ethereum" in headline or "eth" in headline:
            topic = "ethereum"
        elif "defi" in headline:
            topic = "defi"
        elif "ai" in headline or "machine learning" in headline:
            topic = "ai"
        else:
            topic = domain

        key = (topic, domain, sentiment)
        clusters[key].append(a)

    # Convert dict → list of clusters
    return list(clusters.values())
