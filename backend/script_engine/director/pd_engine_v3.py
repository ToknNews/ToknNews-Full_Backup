#!/usr/bin/env python3
"""
pd_engine_v3.py
TOKEN NEWS — 2025 PROGRAM DIRECTOR (PD v3)

Determines:
 - Episode Format
 - Anchor roles (primary / secondary / tertiary)
 - Tone & pacing flags
 - Runtime targets
 - Breaking news triggers (GPT-assisted)
 - Chaos Friday rules
 - Deep Dive selection
 - Smart ad placement signals (ads still disabled by default)

This module outputs a single PD context object consumed
by timeline_builder_v3.
"""

import time
import json
import datetime
from openai import OpenAI

from backend.runtime.vault_loader import load_secrets

secrets = load_secrets()
OPENAI_API_KEY = secrets.get("openai_api_key", "")

client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# RUNTIME TARGETS (from your config)
# ============================================================

RUNTIME_TARGETS_SEC = {
    "morning_brief": 3 * 60,
    "breaking_news": 1 * 60,
    "deep_dive":     5 * 60,
    "standard":     15 * 60,
    "chaos_friday":  7 * 60,
}

# ============================================================
# BREAKING TRIGGERS: Keyword detection
# ============================================================

BREAKING_KEYWORDS = [
    "hack", "exploit", "breach", "drain",
    "rug", "compromised", "attack",
    "liquidation", "selloff", "cascade",
    "flash crash", "emergency", "lawsuit",
    "charged", "sec sues", "filed", "indicted",
]

# ============================================================
# FORMAT DECISION HELPER — GPT-ASSISTED
# ============================================================

def _gpt_assess_urgency(headline: str, summary: str) -> float:
    """
    Returns an urgency score from 0 → 1.
    GPT looks at sentiment, volatility, regulatory significance.
    """
    prompt = f"""
Rate the urgency of this crypto/finance news item from 0 to 1.

Headline: {headline}
Summary: {summary}

Urgency should be:
- High for hacks, exploits, liquidations, regulatory actions, lawsuits, FOMC impact.
- Medium for market volatility or major corporate moves.
- Low for general updates, mild price moves, or opinion pieces.

Only output a decimal number (example: 0.72).
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=5,
            temperature=0,
        )
        score_str = resp.choices[0].message.content.strip()
        return float(score_str)
    except:
        return 0.0


# ============================================================
# DOMAIN WEIGHTS (used to prioritize anchors in formats)
# ============================================================

DOMAIN_PRIORITY = {
    "macro": 1.0,
    "regulation": 1.0,
    "markets": 0.9,
    "defi": 0.8,
    "onchain": 0.8,
    "ai": 0.7,
    "venture": 0.6,
    "culture": 0.4,
    "sentiment": 0.4,
    "general": 0.3,
}

# ============================================================
# TERTIARY ANCHOR RULE (PD-controlled)
# ============================================================

def _maybe_assign_tertiary(domain: str, urgency: float):
    """
    You enabled tertiary anchors ONLY when PD flags.
    That is: high domain heat + high urgency + NOT Breaking
    """
    if domain in ["macro", "regulation"] and urgency > 0.6:
        return "bond"
    if domain in ["defi", "onchain"] and urgency > 0.6:
        return "reef"
    if domain in ["markets"] and urgency > 0.6:
        return "cash"
    return None


# ============================================================
# DAY-BASED LOGIC
# ============================================================

def _is_chaos_friday():
    return datetime.datetime.utcnow().weekday() == 4  # Friday


# ============================================================
# CROSS-SOURCE DUPLICATE DETECTION
# ============================================================

def _is_repeated_story(headline: str, all_stories: list) -> bool:
    count = sum(1 for s in all_stories if headline.lower() in s["headline"].lower())
    return count >= 3


# ============================================================
# PUBLIC API — PD v3 CORE FUNCTION
# ============================================================

def pd_decide_format(story_clusters: list):
    """
    Returns full PD context:
    {
        "format": "breaking_news",
        "target_runtime_sec": 300,
        "primary_anchor": "lawson",
        "secondary_anchor": "ledger",
        "tertiary_anchor": None,
        "chaos_level": 0.0,
        "insert_ad": False,
        "handoff_style": "tight",
    }
    """

    if not story_clusters:
        return {"format": "standard", "target_runtime_sec": RUNTIME_TARGETS_SEC["standard"]}

    # ========================================================
    # STEP 1: SCORE STORIES
    # ========================================================
    scores = []
    for story in story_clusters[:6]:
        headline = story.get("headline", "")
        summary  = story.get("summary", "")
        domain   = story.get("domain", "general")

        urgency = _gpt_assess_urgency(headline, summary)
        repeated = _is_repeated_story(headline, story_clusters)
        breaking_kw = any(k in headline.lower() for k in BREAKING_KEYWORDS)

        # Score structure
        scores.append({
            "headline": headline,
            "summary": summary,
            "domain": domain,
            "urgency": urgency,
            "repeated": repeated,
            "breaking": breaking_kw,
        })

    # ========================================================
    # STEP 2: BREAKING ANALYSIS
    # ========================================================
    for s in scores:
        if s["breaking"]:
            return {
                "format": "breaking_news",
                "target_runtime_sec": RUNTIME_TARGETS_SEC["breaking_news"],
                "primary_anchor": "lawson" if s["domain"] == "regulation" else "ledger",
                "secondary_anchor": None,
                "tertiary_anchor": None,
                "chaos_level": 0.0,
                "insert_ad": False,
                "handoff_style": "tight",
            }

        if s["urgency"] > 0.75 or s["repeated"]:
            return {
                "format": "breaking_news",
                "target_runtime_sec": RUNTIME_TARGETS_SEC["breaking_news"],
                "primary_anchor": "chip",
                "secondary_anchor": None,
                "tertiary_anchor": None,
                "chaos_level": 0.0,
                "insert_ad": False,
                "handoff_style": "tight",
            }

    # ========================================================
    # STEP 3: CHAOS FRIDAY
    # ========================================================
    if _is_chaos_friday():
        return {
            "format": "chaos_friday",
            "target_runtime_sec": RUNTIME_TARGETS_SEC["chaos_friday"],
            "primary_anchor": "bitsy",
            "secondary_anchor": "cash",
            "tertiary_anchor": None,
            "chaos_level": 1.0,
            "insert_ad": False,
            "handoff_style": "loose",
        }

    # ========================================================
    # STEP 4: DEEP DIVE (highest urgency + domain priority)
    # ========================================================
    deep_candidate = max(scores, key=lambda s: DOMAIN_PRIORITY.get(s["domain"], 0) + s["urgency"])
    if deep_candidate["urgency"] > 0.5 and deep_candidate["domain"] in ["macro", "regulation", "ai", "venture"]:
        tertiary = _maybe_assign_tertiary(deep_candidate["domain"], deep_candidate["urgency"])
        return {
            "format": "deep_dive",
            "target_runtime_sec": RUNTIME_TARGETS_SEC["deep_dive"],
            "primary_anchor": deep_candidate["domain"],  # placeholder replaced by timeline
            "secondary_anchor": None,
            "tertiary_anchor": tertiary,
            "chaos_level": 0.0,
            "insert_ad": False,
            "handoff_style": "tight",
        }

    # ========================================================
    # STEP 5: MORNING BRIEF (time-based or calm markets)
    # ========================================================
    utc_hour = datetime.datetime.utcnow().hour
    if 10 <= utc_hour <= 15:
        return {
            "format": "morning_brief",
            "target_runtime_sec": RUNTIME_TARGETS_SEC["morning_brief"],
            "primary_anchor": "chip",
            "secondary_anchor": "cash",
            "tertiary_anchor": None,
            "chaos_level": 0.0,
            "insert_ad": False,
            "handoff_style": "tight",
        }

    # ========================================================
    # DEFAULT: STANDARD
    # ========================================================
    return {
        "format": "standard",
        "target_runtime_sec": RUNTIME_TARGETS_SEC["standard"],
        "primary_anchor": "chip",
        "secondary_anchor": "bond",
        "tertiary_anchor": None,
        "chaos_level": 0.1,
        "insert_ad": False,
        "handoff_style": "normal",
    }

