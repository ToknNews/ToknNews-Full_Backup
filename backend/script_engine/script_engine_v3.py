#!/usr/bin/env python3
"""
script_engine_v3.py
TOKEN NEWS — Clean Script Engine (2025 Architecture)

Responsibilities:
 - Accept fresh enriched stories from ingestion
 - Pass story clusters to timeline_builder
 - Output final script blocks for audio renderer
 - NO GPT logic lives here (all in grok_writer)
 - NO persona logic lives here
 - Purely orchestrates timeline → blocks → return payload

This script engine is intentionally lean.
"""

import time
import uuid

from script_engine.knowledge.episode_builder import build_episode
from script_engine.persona.timeline_builder import build_timeline


# ============================================================
# SCRIPT ENGINE API
# ============================================================

def generate_episode(daypart="evening", show_mode="NEWS"):
    """
    Full script generation pipeline WITHOUT audio.
    Episode Runner will handle TTS + mixing.

    Returns:
      {
        "episode_id": "...",
        "blocks": [...],
        "timestamp": ...
      }
    """

    # -----------------------------------------------
    # 1. Build story clusters (ranked from episode_builder)
    # -----------------------------------------------
    episode_data = build_episode()

    if "error" in episode_data:
        return {"error": "no stories available"}

    story_clusters = episode_data.get("rundown", [])
    episode_id = episode_data.get("episode_id", f"ep_{uuid.uuid4().hex[:8]}")

    # -----------------------------------------------
    # 2. Build timeline (using PD + runtime engines)
    # -----------------------------------------------
    timeline = build_timeline(
        story_clusters,
        daypart=daypart,
        show_mode=show_mode
    )

    blocks = timeline["blocks"]

    # -----------------------------------------------
    # 3. Wrap up
    # -----------------------------------------------
    return {
        "episode_id": episode_id,
        "blocks": blocks,
        "timestamp": time.time(),
        "story_count": len(story_clusters)
    }


# ============================================================
# Self-test
# ============================================================

if __name__ == "__main__":
    test = generate_episode(daypart="evening")
    print("\n=== SCRIPT ENGINE RESULT ===")
    print("Episode ID:", test.get("episode_id"))
    print("Block Count:", len(test.get("blocks", [])))
