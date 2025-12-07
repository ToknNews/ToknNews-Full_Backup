#!/usr/bin/env python3
"""
meta_enrich.py
ToknNews V2 — Story Meta-Enrichment Engine

Adds:
 - why_it_matters
 - narrative_cluster
 - risk_angle
 - smart_money_view
 - anchor_relevance
 - trend_context
"""

from openai import OpenAI
from backend.runtime.vault_loader import load_secrets

_secrets = load_secrets()
client = OpenAI(api_key=_secrets.get("openai_api_key","")) if _secrets.get("openai_api_key") else None


def meta_enrich(story):
    """
    Add deeper editorial metadata to the enriched story.
    """

    if client is None:
        # fallback: generic metadata
        story["meta"] = {
            "why_it_matters": "This relates to general market sentiment.",
            "narrative_cluster": "market_flow",
            "risk_angle": "neutral",
            "smart_money_view": "unclear positioning",
            "anchor_relevance": {
                "chip": 1.0, "bond": 0.6, "cash": 0.6,
                "ledger": 0.4, "neura": 0.3, "bitsy": 0.2
            },
            "trend_context": "moderate relevance"
        }
        return story

    headline = story.get("headline","")
    summary  = story.get("summary","")
    domain   = story.get("domain","general")

    prompt = f"""
You are enriching a crypto/markets news story for ToknNews.

Story:
Headline: {headline}
Summary: {summary}
Domain: {domain}

Provide JSON with these fields:

why_it_matters:
  One sentence that explains the core importance of the story.

narrative_cluster:
  A short label grouping this story into a broader theme
  (examples: liquidity_shift, regulatory_pressure, ai_expansion,
   defi_momentum, risk_off, risk_on, whale_activity, infra_upgrade)

risk_angle:
  One word: positive, negative, or neutral.

smart_money_view:
  One sentence from the perspective of professional traders or institutions.

anchor_relevance:
  Mapping of ToknNews anchors by relevance (0–1 scale).
  Anchors: chip, bond, cash, lawson, ledger, neura, reef, bitsy, penny, rex.

trend_context:
  Short phrase indicating where this story fits into ongoing trends.

Format output ONLY as JSON.
""".strip()

    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            max_tokens=300,
            temperature=0.2,
            timeout=12
        )

        import json
        meta = json.loads(rsp.choices[0].message.content)
        story["meta"] = meta
        return story

    except Exception as e:
        story["meta"] = {
            "why_it_matters": "Unclear importance.",
            "narrative_cluster": "general",
            "risk_angle": "neutral",
            "smart_money_view": "unclear positioning",
            "anchor_relevance": {"chip":1.0},
            "trend_context": "general"
        }
        return story


if __name__ == "__main__":
    print("Meta Enrich Engine Loaded.")
