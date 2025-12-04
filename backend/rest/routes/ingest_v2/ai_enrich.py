#!/usr/bin/env python3
"""
ai_enrich.py
TOKNNews — AI Enrichment Layer (2025)

Adds:
 - GPT headline summary
 - GPT domain classification
 - GPT sentiment scoring
"""

from backend.runtime.vault_loader import load_secrets
from openai import OpenAI
import re

secrets = load_secrets()
client = OpenAI(api_key=secrets.get("openai_api_key", ""))

### --- GPT HELPERS -----------------------------------------

def gpt_call(prompt, max_tokens=120):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.2
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("[AI_ENRICH] ERROR:", e)
        return ""

### --- SUMMARY ----------------------------------------------

def summarize(headline, body=""):
    prompt = f"""
Summarize this crypto news story in 2 sentences max.

Headline: {headline}

Body:
{body[:2000]}
"""
    return gpt_call(prompt)

### --- DOMAIN -----------------------------------------------

def classify_domain(headline, body=""):
    prompt = f"""
Classify this story into ONE domain from the list:
[macro, markets, regulation, defi, onchain, ai, venture, retail, culture, security].

Headline: {headline}
Body: {body[:1000]}

Respond with ONLY the domain name.
"""
    out = gpt_call(prompt, max_tokens=10).lower()
    # sanity fallback
    if out not in ["macro","markets","regulation","defi","onchain","ai","venture","retail","culture","security"]:
        return "markets"
    return out

### --- SENTIMENT --------------------------------------------

def sentiment_score(headline, body=""):
    prompt = f"""
Rate the sentiment of this crypto news story as:
[Positive, Neutral, Negative].

Headline: {headline}
Body: {body[:800]}
"""
    out = gpt_call(prompt, max_tokens=10)
    if "pos" in out.lower(): return "Positive"
    if "neg" in out.lower(): return "Negative"
    return "Neutral"

### --- PUBLIC ENTRY POINT -----------------------------------

def enrich_ai(story):
    headline = story.get("headline", "")
    body = story.get("body", "")

    # Generate missing fields
    story["summary"]   = summarize(headline, body)
    story["domain"]    = classify_domain(headline, body)
    story["sentiment"] = sentiment_score(headline, body)

    return story
