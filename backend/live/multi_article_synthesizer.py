#!/usr/bin/env python3
"""
ToknNews Multi-Article Synthesizer (v1)

Takes 2–N enriched article dicts on the same topic and produces
a single synthesized "cluster view" that Script Engine can use
for deeper analysis.

This version is deterministic and summary-based only.
Later we can swap in OpenAI calls without changing callers.
"""

from collections import Counter


def synthesize_cluster(articles):
    """
    articles: list[dict] with keys like:
      - headline
      - summary
      - source
      - sentiment
      - importance
      - domain

    Returns a dict:
      {
        "cluster_headline": str,
        "combined_summary": str,
        "key_points": list[str],
        "consensus_sentiment": str,
        "avg_importance": float,
        "sources": list[str],
      }
    """

    if not articles:
        return {}

    # Basic fields
    headlines = [a.get("headline", "").strip() for a in articles if a.get("headline")]
    summaries = [a.get("summary", "").strip() for a in articles if a.get("summary")]
    sentiments = [a.get("sentiment", "neutral") for a in articles]
    importance_vals = [a.get("importance", 5) for a in articles]
    sources = [a.get("source", "unknown") for a in articles]

    # 1. Cluster headline: use first non-empty or join top 2
    if headlines:
        cluster_headline = headlines[0]
    else:
        cluster_headline = "Clustered story"

    # 2. Combined summary: join top N summaries
    # (Later: let OpenAI rewrite this into a proper paragraph)
    combined_summary = " ".join(summaries[:3]).strip()

    # 3. Key points: naive splitting into bullets for now
    key_points = []
    for s in summaries[:5]:
        parts = s.split(".")
        for p in parts:
            p = p.strip()
            if len(p) > 40:
                key_points.append(p)

    # Deduplicate key points a bit
    seen = set()
    deduped_points = []
    for p in key_points:
        if p not in seen:
            seen.add(p)
            deduped_points.append(p)

    # 4. Consensus sentiment (majority vote)
    sentiment_counts = Counter(sentiments)
    consensus_sentiment, _ = sentiment_counts.most_common(1)[0]

    # 5. Avg importance
    avg_importance = sum(importance_vals) / max(len(importance_vals), 1)

    return {
        "cluster_headline": cluster_headline,
        "combined_summary": combined_summary,
        "key_points": deduped_points[:6],
        "consensus_sentiment": consensus_sentiment,
        "avg_importance": round(avg_importance, 2),
        "sources": list(set(sources)),
    }
