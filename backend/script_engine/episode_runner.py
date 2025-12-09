#!/usr/bin/env python3
"""
episode_runner.py — ToknNews Episode Orchestrator v5
-----------------------------------------------------

Responsibilities:
- Load fresh enriched stories (or cached stories)
- Apply show-mode routing (NEWS, BREAKING, CHAOS, LATE_NIGHT, etc.)
- Build timeline via TimelineBuilder v5
- Create audio via TTS (only after approval)
- Create Unreal cue packages
- Support:
    • Manual generation (Studio)
    • Approval gating (“Degen Approved”)
    • Autonomous 24/7 mode
    • Breaking-news instant episodes
"""

import os, time, json, uuid
from pathlib import Path

from backend.rest.routes.ingest_v2.ingest_controller import run_ingestion
from backend.script_engine.persona.pd_engine_v45 import pd_engine
from backend.script_engine.persona.timeline_builder import build_timeline
from backend.script_engine.audio.audio_block_renderer import render_audio_blocks
from backend.render_controller import render_episode
from backend.runtime.vault_loader import load_secrets


# -------------------------------------------------------
# DIRECTORIES
# -------------------------------------------------------

BASE_DIR = "/opt/toknnews"
EPISODE_DIR = Path(f"{BASE_DIR}/data/episodes")
BLOCK_DIR   = Path(f"{BASE_DIR}/data/blocks")
UE_DIR      = Path(f"{BASE_DIR}/data/unreal")

EPISODE_DIR.mkdir(parents=True, exist_ok=True)
BLOCK_DIR.mkdir(parents=True, exist_ok=True)
UE_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------
# SECRETS + TOGGLES
# -------------------------------------------------------

_secrets   = load_secrets()
AUTO_MODE  = os.getenv("AUTONOMOUS_MODE", "false").lower() == "true"
ENABLE_TTS = os.getenv("ENABLE_TTS", "false").lower() == "true"


# -------------------------------------------------------
# SAVE UTILITIES
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
# APPROVAL STATE (Studio)
# -------------------------------------------------------

def save_pending_script(episode_id, blocks):
    """Saved before approval. Not rendered yet."""
    preview_path = EPISODE_DIR / f"{episode_id}_preview.json"
    preview_path.write_text(json.dumps(blocks, indent=2))
    return str(preview_path)


# -------------------------------------------------------
# MAIN EPISODE GENERATION (NO AUDIO YET)
# -------------------------------------------------------

def generate_episode_script(episode_id=None, skip_ingest=False):
    """
    Returns:
        {
           episode_id: ...,
           mode: ...,
           blocks: [...],
           metadata_file: ...,
           preview_file: ...
        }
    """

    print("\n=== [EpisodeRunner v5] GENERATING SCRIPT ===")

    # ------- Load or Ingest -------
    if skip_ingest:
        print("[ER] Using cached stories (skip_ingest=True)")
        cache_path = f"{BASE_DIR}/data/rolling_stories.json"
        raw = json.load(open(cache_path, "r"))
        stories = raw if isinstance(raw, list) else raw.get("rundown", [])
    else:
        print("[ER] Ingesting fresh stories…")
        stories = run_ingestion()

    if not stories:
        print("[ER] ERROR: No stories available.")
        return None

    # ------- Show Mode Router -------
    pd_out = pd_engine(stories)
    mode   = pd_out["mode"]
    cap    = pd_out["story_cap"]
    used   = stories[:cap]

    episode_id = episode_id or f"ep_{uuid.uuid4().hex[:8]}"

    # ------- Build Timeline -------
    timeline = build_timeline(used, show_mode=mode)
    blocks       = timeline["blocks"]
    audio_blocks = timeline["audio_blocks"]
    runtime_sec  = timeline["estimated_runtime_sec"]

    print(f"[ER] Script Blocks: {len(blocks)}")
    print(f"[ER] Estimated Runtime: {round(runtime_sec/60,2)} minutes")
    print(f"[ER] Mode: {mode} (cap={cap})")

    # ------- Save Script Preview -------
    preview_file = save_pending_script(episode_id, blocks)

    # ------- Save Metadata -------
    metadata_file = save_episode_metadata(episode_id, {
        "episode_id": episode_id,
        "mode": mode,
        "story_cap": cap,
        "story_count": len(stories),
        "used_story_count": len(used),
        "runtime_sec": runtime_sec,
        "preview_file": preview_file,
        "audio": None,
    })

    return {
        "episode_id": episode_id,
        "mode": mode,
        "blocks": blocks,
        "metadata_file": metadata_file,
        "preview_file": preview_file,
        "audio_blocks": audio_blocks,
    }


# -------------------------------------------------------
# APPROVAL: TRIGGER AUDIO + RENDER + UE PACKAGE
# -------------------------------------------------------

def approve_and_render(episode_id, audio_blocks):
    """
    Called after manual approval (“Degen Approved”)
    """

    print(f"\n=== [EpisodeRunner v5] APPROVED → Rendering Episode {episode_id} ===")

    # ----------- AUDIO RENDERING -----------
    if ENABLE_TTS:
        print("[ER] TTS ENABLED → Rendering audio…")
        final_audio = render_audio_blocks(episode_id, audio_blocks)
    else:
        print("[ER] TTS DISABLED → Skipping audio.")
        final_audio = None

    # ----------- VIDEO / UE PACKAGE -----------
    mp4_path = render_episode(audio_blocks, final_audio, episode_id, mode="unreal")

    print(f"[ER] RENDER COMPLETE → {mp4_path}\n")

    return {
        "episode_id": episode_id,
        "audio": final_audio,
        "video": mp4_path,
    }


# -------------------------------------------------------
# AUTONOMOUS 24/7 LOOP
# -------------------------------------------------------

def autonomous_loop():
    print("\n=== ToknNews Autonomous 24/7 Mode Enabled ===")

    while True:
        ep = generate_episode_script()

        # no approval needed in autonomous mode
        approve_and_render(ep["episode_id"], ep["audio_blocks"])

        print("[ER] Sleeping before next cycle…\n")
        time.sleep(1200)  # 20 minutes


if __name__ == "__main__":
    if AUTO_MODE:
        autonomous_loop()
    else:
        print("EpisodeRunner v5 ready (manual mode).")
