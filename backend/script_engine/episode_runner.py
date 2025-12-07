#!/usr/bin/env python3
"""
episode_runner.py
ToknNews V2 — Episode Runtime Engine with:
 - Show Mode Routing
 - Story Cap
 - Hybrid Runtime Estimation
 - Audio Disabled (until V2 Audio Engine is rebuilt)
"""

import os, time, json, uuid
from pathlib import Path

from backend.rest.routes.ingest_v2.ingest_controller import run_ingestion
from backend.script_engine.show_modes.router import determine_show_mode
from backend.script_engine.persona.timeline_builder import build_timeline

BASE_DIR = "/opt/toknnews"
EPISODE_CACHE = f"{BASE_DIR}/data/rolling_stories.json"
EPISODE_DIR   = Path(f"{BASE_DIR}/data/episodes")
BLOCK_DIR     = Path(f"{BASE_DIR}/data/blocks")

EPISODE_DIR.mkdir(parents=True, exist_ok=True)
BLOCK_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------
# Saving Utilities
# -------------------------------------------------------

def save_blocks_json(episode_id, blocks):
    path = BLOCK_DIR / f"{episode_id}_blocks.json"
    path.write_text(json.dumps(blocks, indent=2))
    return str(path)


def save_episode_metadata(episode_id, metadata):
    path = EPISODE_DIR / f"{episode_id}_meta.json"
    path.write_text(json.dumps(metadata, indent=2))
    return str(path)


# -------------------------------------------------------
# Main Episode Runner
# -------------------------------------------------------

def run_episode(
    episode_id=None,
    skip_ingest=False,
    skip_audio=False,    # Ignored: audio is disabled
    daypart="evening",
    show_mode="AUTO",
    voice_map=None
):
    print("\n============================")
    print("[EpisodeRunner] Starting episode")
    print("============================\n")

    # ---------------------------------------------------
    # LOAD OR INGEST
    # ---------------------------------------------------
    if skip_ingest:
        print("[EpisodeRunner] skip_ingest=True → loading cached stories…")
        raw = json.load(open(EPISODE_CACHE, "r"))
        stories = raw if isinstance(raw, list) else raw.get("rundown", [])
        if not stories:
            print("[EpisodeRunner] ERROR: No cached stories.")
            return None
    else:
        print("[EpisodeRunner] skip_ingest=False → performing ingestion")
        stories = run_ingestion()

    print(f"[EpisodeRunner] Story Count: {len(stories)}")

    # ---------------------------------------------------
    # SHOW MODE ROUTER
    # ---------------------------------------------------
    router_output = determine_show_mode(stories)
    mode = router_output["mode"]
    cap  = router_output["story_cap"]

    print(f"[EpisodeRunner] Mode: {mode} (cap={cap}, override={router_output['override']})")

    # Cap stories BEFORE PD & timeline
    selected_stories = stories[:cap]

    # Episode ID
    episode_id = episode_id or f"ep_{uuid.uuid4().hex[:8]}"

    # ---------------------------------------------------
    # TIMELINE BUILD
    # ---------------------------------------------------
    pkg = build_timeline(
        selected_stories,
        daypart=daypart,
        show_mode=mode,
        voice_map=voice_map
    )

    blocks       = pkg["blocks"]
    audio_blocks = pkg["audio_blocks"]
    est_runtime  = pkg["estimated_runtime_sec"]

    print(f"[EpisodeRunner] Blocks: {len(blocks)}")
    print(f"[EpisodeRunner] Estimated Runtime: {round(est_runtime/60, 2)} minutes")

    # ---------------------------------------------------
    # AUDIO DISABLED (V2 Audio Engine coming later)
    # ---------------------------------------------------
    final_audio_path = None
    print("[EpisodeRunner] AUDIO DISABLED — skipping all audio rendering.")

    # ---------------------------------------------------
    # SAVE FILES
    # ---------------------------------------------------
    blocks_path = save_blocks_json(episode_id, blocks)
    meta_path   = save_episode_metadata(episode_id, {
        "episode_id": episode_id,
        "timestamp": time.time(),
        "mode": mode,
        "story_cap": cap,
        "story_count": len(stories),
        "used_story_count": len(selected_stories),
        "blocks_file": blocks_path,
        "estimated_runtime_sec": est_runtime,
        "router": router_output
    })

    print("\n[EpisodeRunner] Episode complete.\n")

    return {
        "episode_id": episode_id,
        "mode": mode,
        "stories_used": len(selected_stories),
        "blocks": blocks,
        "metadata_file": meta_path,
        "blocks_file": blocks_path,
        "estimated_runtime_sec": est_runtime,
        "audio": None
    }


if __name__ == "__main__":
    run_episode()
