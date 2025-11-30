#!/usr/bin/env python3
"""
synthesis_engine.py
TOKNNews — Multi-Article GPT Synthesis Engine

This module generates a unified synthesis paragraph for a given headline
and its related cluster_articles. The synthesis is short, factual, and
designed to feed the timeline builder with context.

GPT-first design. Deterministic fallback included.
"""

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ------------------------------------------------------------
# Helper: Fallback synthesis if GPT fails
# ------------------------------------------------------------
def fallback_synthesis(headline: str, cluster_articles: list) -> str:
    parts = [headline]
    parts.extend(cluster_articles)
    summary = " ".join(parts)
    return f"Summary unavailable. Key points: {summary[:220]}..."


# ------------------------------------------------------------
# GPT Synthesis
# ------------------------------------------------------------
def gpt_synthesize(headline: str, cluster_articles: list) -> str:
    """
    Use GPT-4o-mini to generate a 2–4 sentence synthesis that:
        - stays factual
        - avoids hype
        - merges related context cleanly
        - never fabricates unknown details
    """
    try:
        related = "\n".join(f"- {c}" for c in cluster_articles) if cluster_articles else "None"

        prompt = f"""
You are the synthesis engine for Token News. Your job is to generate a
neutral, concise, 2–4 sentence synthesis combining the headline and
related articles.

HEADLINE:
{headline}

RELATED ARTICLES:
{related}

RULES:
- Remain factual based on the text only.
- Combine ideas into a single coherent narrative.
- Do NOT add extra details not explicitly provided.
- Tone: neutral, newsroom, clean.
- No sensationalism or hype.
- No bullet points — output a paragraph.

Output ONLY the synthesis paragraph.
"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=180,
            temperature=0.3
        )

        text = resp.choices[0].message.content.strip()
        return text

    except Exception as e:
        print("[SynthesisEngine] GPT failure:", e)
        return fallback_synthesis(headline, cluster_articles)


# ------------------------------------------------------------
# Public API
# ------------------------------------------------------------
def build_synthesis(headline: str, cluster_articles: list) -> str:
    """
    Entrypoint. Always returns a synthesis, GPT or fallback.
    """
    return gpt_synthesize(headline, cluster_articles)


# ------------------------------------------------------------
# Test Mode
# ------------------------------------------------------------
if __name__ == "__main__":
    example = build_synthesis(
        "Ethereum ETF filings accelerate after SEC review",
        [
            "BlackRock updates Ethereum ETF structure",
            "Grayscale meets SEC regarding ETH futures product"
        ]
    )
    print(example)
