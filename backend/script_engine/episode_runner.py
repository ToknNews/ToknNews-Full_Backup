#!/usr/bin/env python3
"""
episode_runner.py
TOKEN NEWS — Full Episode Runner (2025 Runtime-PD Architecture)
"""

import os
import time
import json
import uuid

from script_engine.knowledge.episode_builder import build_episode
from backend.script_engine.persona.timeline_builder import build_timeline
from script_engine.audio.audio_block_renderer import render_audio_blocks
from backend.runtime.vault_loader import load_secrets
secrets = load_secrets()

BASE_DIR = "/opt/toknnews"
OUTPUT_DIR = f"{BASE_DIR}/output"
AUDIO_DIR  = f"{BASE_DIR}/data/audio"
EPISODE_DIR = f"{BASE_DIR}/data/episodes"
BLOCK_EXPORT_DIR = f"{BASE_DIR}/data/blocks"
EPISODE_CACHE = f"{BASE_DIR}/data/rolling_stories.json"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(EPISODE_DIR, exist_ok=True)
os.makedirs(BLOCK_EXPORT_DIR, exist_ok=True)

def save_blocks_json(episode_id, blocks):
    path = f"{BLOCK_EXPORT_DIR}/{episode_id}_blocks.json"
    with open(path, "w") as f:
        json.dump(blocks, f, indent=2)
    return path

def save_episode_metadata(episode_id, metadata):
    path = f"{EPISODE_DIR}/{episode_id}_meta.json"
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return path

def run_episode(episode_id="dev", skip_ingest=False, daypart="evening", show_mode="NEWS"):
    print("\n\n============================")
    print(f"[EpisodeRunner] Starting episode: {episode_id}")
    print("============================\n")

    if skip_ingest:
        try:
            with open(EPISODE_CACHE, "r") as f:
                story_clusters = json.load(f)["rundown"]
        except Exception as e:
            print(f"[EpisodeRunner] ERROR: Cannot load cached stories: {e}")
            return None
    else:
        episode_data = build_episode()
        if "error" in episode_data:
            print("[EpisodeRunner] ERROR: No stories available.")
            return None
        story_clusters = episode_data.get("rundown", [])
        episode_id = episode_data.get("episode_id", episode_id)

    print(f"[EpisodeRunner] Story Count: {len(story_clusters)}")

    timeline_package = build_timeline(
        story_clusters,
        daypart=daypart,
        show_mode=show_mode
    )

    blocks = timeline_package["blocks"]
    print(f"[EpisodeRunner] Timeline blocks: {len(blocks)}")

    audio_scene_id = f"{episode_id}_speech"
    print("[EpisodeRunner] Rendering audio blocks…")

    final_audio_path = render_audio_blocks(
        scene_id=audio_scene_id,
        audio_blocks=blocks
    )

    if not final_audio_path:
        print("[EpisodeRunner] WARNING: Audio render failed.")
    else:
        print(f"[EpisodeRunner] Final audio path: {final_audio_path}")

    blocks_path = save_blocks_json(episode_id, blocks)
    meta_path = save_episode_metadata(episode_id, {
        "episode_id": episode_id,
        "timestamp": time.time(),
        "story_count": len(story_clusters),
        "block_count": len(blocks),
        "audio_file": final_audio_path,
        "blocks_file": blocks_path
    })

    print(f"[EpisodeRunner] Metadata saved → {meta_path}")
    print("\n[EpisodeRunner] Episode complete.\n")

    return {
        "episode_id": episode_id,
        "audio": final_audio_path,
        "blocks": blocks,
        "metadata_file": meta_path,
        "blocks_file": blocks_path
    }

if __name__ == "__main__":
    run_episode()
