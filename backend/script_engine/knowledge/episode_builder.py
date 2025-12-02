#!/usr/bin/env python3
"""
TOKNNews — Episode Builder
Transforms ranked stories into a 20-minute broadcast episode.
"""

import json
import time
import os
from script_engine.knowledge.rank_stories import rank_stories
from loguru import logger

ROLLING_PATH = "/opt/toknnews/data/rolling_stories.json"
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
    domain = (domain or "sentiment").lower()
    return DOMAIN_ANCHORS.get(domain, ["chip"])

def build_episode(rundown_count=6):
    stories = load_rolling()
    if not stories:
        return {"error": "no stories available"}

    ranked = rank_stories(stories)
    rundown = ranked[:rundown_count]
    deep_dive = ranked[0]

    episode = {
        "timestamp": time.time(),
        "episode_id": f"episode_{int(time.time())}",
        "rundown_count": rundown_count,
        "rundown": [],
        "deep_dive": {},
        "segments": []
    }

    for s in rundown:
        domain = s.get("domain", "sentiment")
        episode["rundown"].append({
            "headline":   s.get("headline", ""),
            "summary":    s.get("summary", ""),
            "domain":     domain,
            "importance": s.get("importance", 5),
            "sentiment":  s.get("sentiment", "Neutral"),
            "rank_score": s.get("rank_score", 0),
            "anchors":    choose_anchors(domain)
        })

    domain = deep_dive.get("domain", "sentiment")
    episode["deep_dive"] = {
        "headline":   deep_dive.get("headline", ""),
        "summary":    deep_dive.get("summary", ""),
        "domain":     domain,
        "importance": deep_dive.get("importance", 5),
        "sentiment":  deep_dive.get("sentiment", "Neutral"),
        "rank_score": deep_dive.get("rank_score", 0),
        "anchors":    choose_anchors(domain)
    }

    segments = []

    segments.append({
        "type": "chip_rundown",
        "stories": episode["rundown"]
    })

    segments.append({
        "type": "deep_dive",
        "story": episode["deep_dive"]
    })

    episode["segments"] = segments

    # Save episode to disk
    episode_path = f"/opt/toknnews/data/episodes/{episode['episode_id']}.json"
    os.makedirs(os.path.dirname(episode_path), exist_ok=True)
    with open(episode_path, "w") as f:
        json.dump(episode, f, indent=2)
    logger.info(f"[episode_builder] Episode saved to {episode_path}")

    return episode
