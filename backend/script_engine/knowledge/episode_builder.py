#!/usr/bin/env python3
"""
TOKNNews — Episode Builder
Transforms ranked stories into a 20-minute broadcast episode.

Steps:
 - Load rolling stories
 - Rank them using rank_stories()
 - Select Chip’s rundown (top 5–7)
 - Select deep-dive story (#1)
 - Assign anchors based on domain
 - Build PD-ready episode structure
 - Save to /data/episodes/episode_<timestamp>.json
"""

import json
import time
import os
from .rank_stories import rank_stories

ROLLING_PATH = "/opt/toknnews/data/stories/latest.json"
EPISODE_DIR = "/var/www/toknnews-live/data/episodes"

DOMAIN_ANCHORS = {
    "macro": ["bond"],
    "markets": ["cash", "bond"],
    "legal": ["lawson"],
    "defi": ["reef"],
    "onchain": ["ledger"],
    "ai": ["neura"],
    "venture": ["cap"],
    "retail": ["penny"],
    "culture": ["bitsy"],
    "sentiment": ["ivy", "cash"],
    "general": ["chip"]
}


def load_rolling():
    try:
        with open(ROLLING_PATH, "r") as f:
            return json.load(f)
    except Exception as e:
        print("[episode_builder] ERROR loading rolling stories:", e)
        return []


def choose_anchors(domain: str):
    domain = (domain or "general").lower()
    return DOMAIN_ANCHORS.get(domain, ["chip"])


def build_episode(rundown_count=6):
    stories = load_rolling()

    if not stories:
        return {"error": "no stories available"}

    # Rank stories using editorial logic
    ranked = rank_stories(stories)

    # Chip rundown: top N (default 6)
    rundown = ranked[:rundown_count]

    # Deep dive = #1 story
    deep_dive = ranked[0]

    # Build episode block
    episode = {
        "timestamp": time.time(),
        "episode_id": f"episode_{int(time.time())}",
        "rundown_count": rundown_count,
        "rundown": [],
        "deep_dive": {},
        "segments": []
    }

    # Chip rundown entries
    for s in rundown:
        episode["rundown"].append({
            "headline": s["headline"],
            "summary": s.get("summary", s["headline"][:120] + "..."),
            "domain": s["domain"],
            "importance": s["importance"],
            "sentiment": s["sentiment"],
            "rank_score": s["rank_score"],
            "anchors": choose_anchors(s["domain"])
        })

    # Deep dive block
    episode["deep_dive"] = {
        "headline": deep_dive["headline"],
        "summary": deep_dive["summary"],
        "domain": deep_dive["domain"],
        "sentiment": deep_dive["sentiment"],
        "importance": deep_dive["importance"],
        "rank_score": deep_dive["rank_score"],
        "anchors": choose_anchors(deep_dive["domain"])
    }

    # Segment plan (PD-ready)
    # 1. Chip rundown
    # 2. Deep dive
    # 3. Domain analysis blocks
    # 4. Vega color if volatility or breaking
    # 5. Bitsy sentiment if culture/spike

    segments = []

    # Chip rundown segment
    segments.append({
        "type": "chip_rundown",
        "stories": episode["rundown"]
    })

    # Deep dive segment
    segments.append({
        "type": "deep_dive",
        "story": episode["deep_dive"]
    })

    # Additional anchor segments
    for s in ranked[1:5]:
        segments.append({
            "type": "anchor_analysis",
            "headline": s["headline"],
            "domain": s["domain"],
            "anchors": choose_anchors(s["domain"]),
            "summary": s.get("summary", s["headline"][:120] + "..."),
            "importance": s["importance"]
        })

    episode["segments"] = segments

    return episode


def save_episode(ep):
    os.makedirs(EPISODE_DIR, exist_ok=True)
    path = os.path.join(EPISODE_DIR, ep["episode_id"] + ".json")

    with open(path, "w") as f:
        json.dump(ep, f, indent=2)

    return path


if __name__ == "__main__":
    ep = build_episode()
    p = save_episode(ep)
    print("[Episode Saved]", p)
