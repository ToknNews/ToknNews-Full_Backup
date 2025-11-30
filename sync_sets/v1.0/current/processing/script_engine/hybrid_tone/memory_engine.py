#!/usr/bin/env python3
"""
memory_engine.py
Stores + retrieves short-term memory for tone, domains, sentiment streaks,
and anchor pairing reinforcement.
"""

import random

# ---------------------------------------------------------
# Sentiment-memory (very lightweight)
# ---------------------------------------------------------
def summarize_recent_sentiment(recent_stories):
    if not recent_stories:
        return None

    sentiments = [s.get("sentiment", "neutral") for s in recent_stories]
    pos = sentiments.count("positive")
    neg = sentiments.count("negative")
    neu = sentiments.count("neutral")

    if neg > pos and neg > neu:
        return "recent sentiment has been mostly negative"
    if pos > neg and pos > neu:
        return "recent sentiment has been mostly positive"
    return "recent sentiment has been mixed"


# ---------------------------------------------------------
# Domain clustering (used for theme + synthesis)
# ---------------------------------------------------------
def summarize_recent_domains(recent_stories):
    if not recent_stories:
        return None

    domains = [s.get("domain", "general") for s in recent_stories]
    freq = {}
    for d in domains:
        freq[d] = freq.get(d, 0) + 1

    # find most frequent domain
    main = max(freq, key=freq.get)
    return main


# ---------------------------------------------------------
# Anchor relationship emphasis (lightweight personality link)
# ---------------------------------------------------------
def anchor_relationship_hint(primary, secondary=None):
    if not primary:
        return None

    hints = {
        "Lawson Black": "Chip tends to lean on Lawson for regulatory clarity.",
        "Reef Gold": "Chip likes letting Reef unpack DeFi mechanics.",
        "Neura Grey": "Neura usually brings the technical layer Chip relies on.",
        "Cap Silver": "Chip knows Cap will frame this like a funding round.",
        "Bitsy Gold": "Bitsy brings the cultural spin Chip can't predict.",
        "Ledger Stone": "Ledger’s data-first lens keeps things grounded.",
    }

    if primary in hints:
        return hints[primary]

    return None


# ---------------------------------------------------------
# Build a single memory summary line for Chip
# ---------------------------------------------------------
def build_memory_overlay(enriched):
    """
    Produces ONE optional overlay line Chip can drop right after his toss,
    based on recent story memory.
    """

    recent = enriched.get("recent_stories", [])
    if not recent:
        return None

    # sentiment wrap
    sentiment_line = summarize_recent_sentiment(recent)

    # domain trend
    domain = summarize_recent_domains(recent)

    # anchor pair hint
    relationship_line = anchor_relationship_hint(
        enriched.get("primary_character"),
        enriched.get("secondary_character")
    )

    # Build candidate lines
    lines = []

    if sentiment_line:
        lines.append(f"Quick context: {sentiment_line}.")
    if domain:
        lines.append(f"Trend-wise, {domain} topics have been showing up repeatedly.")
    if relationship_line:
        lines.append(relationship_line)

    if not lines:
        return None

    return random.choice(lines)
