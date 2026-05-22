#!/usr/bin/env python3
"""
meta_enrich.py
ToknNews — Editorial Meta Enrichment Engine
"""

import os
import json
import openai
from backend.runtime.vault_loader import load_secrets

load_secrets()
openai.api_key = os.getenv("OPENAI_API_KEY")


def meta_enrich(story):

    headline = story.get("headline", "")
    summary = story.get("summary", "")
    domain = story.get("domain", "general")

    semantic = story.get("semantic_keys", {})
    assets = semantic.get("assets", [])
    event_type = semantic.get("event_type")

    tokn = story.get("toknclaw_context", {})
    metrics = tokn.get("metrics")
    memory = tokn.get("memory")
    deltas = tokn.get("deltas")

    fact_capsules = story.get("fact_capsules", [])

    prompt = f"""
You are enriching a crypto / markets news story for a broadcast program.

Story
Headline: {headline}
Summary: {summary}
Domain: {domain}

Assets: {assets}
Event type: {event_type}

ToknClaw Metrics:
{metrics}

ToknClaw Memory:
{memory}

ToknClaw Deltas:
{deltas}

Fact Capsules:
{fact_capsules}

Return JSON with:

why_it_matters
narrative_cluster
risk_angle
smart_money_view
anchor_relevance
trend_context
discussion_angle
meta_confidence

Do not invent facts.
Use the metrics and fact capsules when available.
""".strip()

    try:

        rsp = openai.ChatCompletion.create(
            model="gpt-4.1-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
        )

        meta = json.loads(rsp.choices[0].message.content)

    except Exception:

        meta = {
            "why_it_matters": "Market activity suggests evolving sentiment.",
            "narrative_cluster": "market_flow",
            "risk_angle": "neutral",
            "smart_money_view": "Professional traders are monitoring liquidity and positioning.",
            "anchor_relevance": {
                "chip": 1.0,
                "bond": 0.6,
                "cash": 0.6,
                "ledger": 0.5,
                "neura": 0.4,
                "reef": 0.3,
                "bitsy": 0.2
            },
            "trend_context": "emerging signal",
            "discussion_angle": "market positioning",
            "meta_confidence": 0.5
        }

    story["meta"] = meta

    return story
