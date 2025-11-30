#!/usr/bin/env python3
"""
episode_runner.py
TOKEN NEWS — Full Episode Runner (2025 Runtime-PD Architecture)

Responsibilities:
 - Load ranked stories from episode_builder
 - Build pacing blueprint + runtime goal controller
 - Generate complete timeline (timeline_builder)
 - Render audio for all blocks (audio_block_renderer + mixer)
 - Package final episode output for Unreal / post-processing
"""

import os
import time
import json
import uuid

from script_engine.knowledge.episode_builder import build_episode
from script_engine.persona.timeline_builder import build_timeline
from script_engine.audio.audio_block_renderer import render_audio_blocks
from backend.runtime.vault_loader import load_secrets
secrets = load_secrets()


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = "/opt/toknnews"
OUTPUT_DIR = f"{BASE_DIR}/output"
AUDIO_DIR  = f"{BASE_DIR}/data/audio"
EPISODE_DIR = f"{BASE_DIR}/data/episodes"
BLOCK_EXPORT_DIR = f"{BASE_DIR}/data/blocks"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(EPISODE_DIR, exist_ok=True)
os.makedirs(BLOCK_EXPORT_DIR, exist_ok=True)


# ============================================================
# SAVE BLOCKS TO DISK (JSON)
# ============================================================

def save_blocks_json(episode_id, blocks):
    path = f"{BLOCK_EXPORT_DIR}/{episode_id}_blocks.json"
    with open(path, "w") as f:
        json.dump(blocks, f, indent=2)
    return path


# ============================================================
# SAVE EPISODE METADATA
# ============================================================

def save_episode_metadata(episode_id, metadata):
    path = f"{EPISODE_DIR}/{episode_id}_meta.json"
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return path


# ============================================================
# EPISODE RUNNER
# ============================================================

def run_episode(daypart="evening", show_mode="NEWS"):
    """
    Full episode execution pipeline:
      1. Build story clusters
      2. Build timeline
      3. Render audio
      4. Save everything
    """

    print("\n\n============================")
    print("[EpisodeRunner] Starting new episode cycle…")
    print("============================\n")

    # --------------------------------------------------------
    # 1. Build episode structure (ranked stories, clusters)
    # --------------------------------------------------------
    episode_data = build_episode()

    if "error" in episode_data:
        print("[EpisodeRunner] ERROR: No stories available. Skipping episode.")
        return None

    story_clusters = episode_data.get("rundown", [])
    episode_id = episode_data.get("episode_id", f"ep_{uuid.uuid4().hex[:8]}")

    print(f"[EpisodeRunner] Episode ID: {episode_id}")
    print(f"[EpisodeRunner] Story Count: {len(story_clusters)}")

    # --------------------------------------------------------
    # 2. Build timeline using new PD + runtime engines
    # --------------------------------------------------------
    timeline_package = build_timeline(
        story_clusters,
        daypart=daypart,
        show_mode=show_mode
    )

    blocks = timeline_package["blocks"]
    print(f"[EpisodeRunner] Timeline blocks generated: {len(blocks)}")

    # --------------------------------------------------------
    # 3. Render Audio (full episode speech track)
    # --------------------------------------------------------
    audio_scene_id = f"{episode_id}_speech"
    print("[EpisodeRunner] Rendering audio blocks…")

    final_audio_path = render_audio_blocks(
        scene_id=audio_scene_id,
        audio_blocks=blocks
    )

    if not final_audio_path:
        print("[EpisodeRunner] WARNING: Audio render failed.")
    else:
        print(f"[EpisodeRunner] Final audio file: {final_audio_path}")

    # --------------------------------------------------------
    # 4. Save episode metadata + blocks JSON
    # --------------------------------------------------------
    blocks_path = save_blocks_json(episode_id, blocks)

    metadata = {
        "episode_id": episode_id,
        "timestamp": time.time(),
        "story_count": len(story_clusters),
        "block_count": len(blocks),
        "audio_file": final_audio_path,
        "blocks_file": blocks_path
    }

    meta_path = save_episode_metadata(episode_id, metadata)
    print(f"[EpisodeRunner] Saved episode metadata → {meta_path}")

    print("\n[EpisodeRunner] Episode complete.\n")

    return {
        "episode_id": episode_id,
        "audio": final_audio_path,
        "blocks": blocks,
        "metadata_file": meta_path,
        "blocks_file": blocks_path
    }


# ============================================================
# SELF TEST
# ============================================================

if __name__ == "__main__":
    result = run_episode(daypart="evening")
    print("\n=== RESULT ===")
    print(result)
