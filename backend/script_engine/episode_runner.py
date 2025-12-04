#!/usr/bin/env python3
"""
episode_runner.py
TOKEN NEWS — 2025 PDv3 Episode Runtime Engine
"""

import os, time, json, uuid

from backend.rest.routes.ingest_v2.enrich_v2 import enrich_item
from script_engine.knowledge.episode_builder import build_episode
from backend.script_engine.persona.timeline_builder import build_timeline
from backend.script_engine.runtime_estimator import estimate_block_runtime
from backend.runtime.vault_loader import load_secrets
secrets = load_secrets()

# ============================================================
# PATHS
# ============================================================

BASE_DIR = "/opt/toknnews"
EPISODE_CACHE = f"{BASE_DIR}/data/rolling_stories.json"
EPISODE_DIR   = f"{BASE_DIR}/data/episodes"
BLOCK_DIR     = f"{BASE_DIR}/data/blocks"

os.makedirs(EPISODE_DIR, exist_ok=True)
os.makedirs(BLOCK_DIR, exist_ok=True)

# ============================================================
# SAVE HELPERS
# ============================================================

def save_blocks_json(episode_id, blocks):
    path = f"{BLOCK_DIR}/{episode_id}_blocks.json"
    with open(path, "w") as f:
        json.dump(blocks, f, indent=2)
    return path

def save_episode_metadata(episode_id, metadata):
    path = f"{EPISODE_DIR}/{episode_id}_meta.json"
    with open(path, "w") as f:
        json.dump(metadata, f, indent=2)
    return path

# ============================================================
# MAIN ENTRY — run_episode()
# ============================================================

def run_episode(
    episode_id=None,
    skip_ingest=False,
    skip_audio=False,
    daypart="evening",
    show_mode="NEWS",
    voice_map=None
):
    print("\n============================")
    print(f"[EpisodeRunner] Starting episode: {episode_id or 'auto'}")
    print("============================\n")

    # ============================================================
    # LOAD STORY CLUSTERS (PATCHED)
    # ============================================================

    if skip_ingest:
        print("[EpisodeRunner] skip_ingest=True → loading cached stories…")

        try:
            with open(EPISODE_CACHE, "r") as f:
                raw = json.load(f)

            # NEW: allow cached file to be a list OR dict
            if isinstance(raw, list):
                story_clusters = raw
            else:
                story_clusters = raw.get("rundown", [])

            if not story_clusters:
                print("[EpisodeRunner] ERROR: Cached file has no stories → aborting.")
                return None

            if not episode_id:
                episode_id = f"ep_{uuid.uuid4().hex[:8]}"

        except Exception as e:
            print(f"[EpisodeRunner] ERROR: Cannot load cached stories: {e}")
            return None

    else:
        print("[EpisodeRunner] skip_ingest=False → running episode_builder…")

        episode_data = build_episode()

        if not episode_data or "error" in episode_data:
            print("[EpisodeRunner] ERROR: No stories available from episode_builder.")
            return None

        # NEW: safely extract rundown
        story_clusters = episode_data.get("rundown", [])
        if not story_clusters:
            print("[EpisodeRunner] ERROR: episode_builder returned no rundown stories.")
            return None

        # assign ID (prefer CLI ID)
        episode_id = episode_id or episode_data.get("episode_id")

    print(f"[EpisodeRunner] Story Count: {len(story_clusters)}")

    # --------------------------------------------------------
    # TIMELINE BUILD (PDv3 + GPT)
    # --------------------------------------------------------
    pkg = build_timeline(
        story_clusters,
        daypart=daypart,
        show_mode=show_mode,
        voice_map=voice_map
    )

    blocks = pkg["blocks"]
    pd_context = pkg["pd_context"]
    est_runtime = pkg["estimated_runtime_sec"]

    print(f"[EpisodeRunner] Timeline blocks: {len(blocks)}")
    print(f"[EpisodeRunner] Estimated Runtime: {round(est_runtime/60,2)} minutes")

    # --------------------------------------------------------
    # AUDIO RENDERING (optional)
    # --------------------------------------------------------
    if skip_audio:
        final_audio_path = None
        print("[EpisodeRunner] Audio skipped (skip_audio=True)")
    else:
        from script_engine.audio.audio_block_renderer import render_audio_blocks
        audio_scene_id = f"{episode_id}_speech"
        final_audio_path = render_audio_blocks(
            scene_id=audio_scene_id,
            audio_blocks=blocks
        )
        print(f"[EpisodeRunner] Audio file: {final_audio_path}")

    # --------------------------------------------------------
    # SAVE OUTPUT FILES
    # --------------------------------------------------------
    blocks_path = save_blocks_json(episode_id, blocks)
    meta_path = save_episode_metadata(episode_id, {
        "episode_id": episode_id,
        "timestamp": time.time(),
        "blocks_file": blocks_path,
        "audio_file": final_audio_path,
        "story_count": len(story_clusters),
        "block_count": len(blocks),
        "estimated_runtime_sec": est_runtime,
        "pd_context": pd_context
    })

    print(f"[EpisodeRunner] Metadata saved → {meta_path}")
    print("\n[EpisodeRunner] Episode complete.\n")

    return {
        "episode_id": episode_id,
        "blocks": blocks,
        "audio": final_audio_path,
        "metadata_file": meta_path,
        "blocks_file": blocks_path,
        "pd_context": pd_context,
        "estimated_runtime_sec": est_runtime,
    }


if __name__ == "__main__":
    run_episode()

