# hybrid_tone/anchor_outlook.py
# A-9 — Chip Blue’s Intelligent Summary Engine

import random

# Domain → framing buckets
DOMAIN_FRAMES = {
    "markets": [
        "market structure is shifting",
        "liquidity conditions are tightening",
        "price action remains reactive",
        "participants are watching flows closely",
    ],
    "ai": [
        "innovation pressure is accelerating",
        "competition remains intense in the AI stack",
        "infrastructure demand continues to rise",
        "capex cycles are driving the narrative",
    ],
    "security": [
        "operational risk remains elevated",
        "attack surfaces are expanding",
        "security posture is under scrutiny",
        "teams are watching for downstream impact",
    ],
    "defi": [
        "on-chain liquidity is reshuffling",
        "protocol incentives are influencing activity",
        "yield conditions are moving quickly",
        "participants are eyeing smart-contract risk",
    ],
    "venture": [
        "capital appetite is cyclical here",
        "valuations remain under pressure",
        "investors are selective on quality",
        "funding rotation is still ongoing",
    ],
    "general": [
        "broader sentiment is mixed",
        "signals are still forming",
        "there’s nuance here worth noting",
        "the overall picture is still taking shape",
    ]
}

# Sentiment → tonal direction
SENTIMENT_TONES = {
    "positive": "upside potential remains in focus",
    "neutral": "the picture is mixed but stabilizing",
    "negative": "risk remains the dominant theme",
}

# Importance → pacing
IMPORTANCE_FRAMES = [
    "quick read",
    "notable",
    "important development",
    "major story",
    "one of the day's defining moves"
]


def build_chip_outlook(enriched):
    domain = enriched.get("domain", "general").lower()
    sentiment = enriched.get("sentiment", "neutral").lower()
    importance = int(enriched.get("importance", 5))

    # Pick domain framing
    frames = DOMAIN_FRAMES.get(domain, DOMAIN_FRAMES["general"])
    frame = random.choice(frames)

    # Sentiment tone
    tone = SENTIMENT_TONES.get(sentiment, SENTIMENT_TONES["neutral"])

    # Importance scaling (0–10 → 0–4)
    idx = max(0, min(4, importance // 2))
    importance_tag = IMPORTANCE_FRAMES[idx]

    # Compose natural language
    line = (
        f"Big picture — this is a {importance_tag}: {frame}, and overall {tone}."
    )

    # Clean spacing
    return " ".join(line.split()).replace(" ,", ",")
