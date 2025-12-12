#!/usr/bin/env python3
"""
episode_runner.py — ToknNews Episode Orchestrator v5.2
-----------------------------------------------------

Responsibilities:
- Load enriched stories
- Determine show mode
- Build conversational timeline
- Render TTS blocks (if enabled)
- Stitch final episode audio
- Optional post-render realism (breath overlay)
- Prepare for future video render
"""

import os
import time
import json
import uuid
from pathlib import Path

from backend.rest.routes.ingest_v2.ingest_controller import run_ingestion
from backend.script_engine.persona.pd_engine_v45 import pd_engine
from backend.script_engine.timeline_builder_v5 import build_timeline

from backend.script_engine.audio.audio_block_renderer import render_audio_blocks
from backend.script_engine.audio.episode_audio_stitcher import stitch_episode_audio

from backend.render_controller import render_episode
from backend.runtime.vault_loader import load_secrets


# -------------------------------------------------------
# DIRECTORIES
# -------------------------------------------------------

BASE_DIR = "/opt/toknnews"

EPISODE_DIR = Path(f"{BASE_DIR}/data/episodes")
BLOCK_DIR   = Path(f"{BASE_DIR}/data/blocks")
AUDIO_DIR   = Path(f"{BASE_DIR}/data/audio_blocks")

EPISODE_DIR.mkdir(parents=True, exist_ok=True)
BLOCK_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# -------------------------------------------------------
# SECRETS + TOGGLES
# -------------------------------------------------------

_secrets = load_secrets()

AUTO_MODE  = os.getenv("AUTONOMOUS_MODE", "false").lower() == "true"
ENABLE_TTS = os.getenv("ENABLE_TTS", "false").lower() == "true"

# realism toggle (safe default)
ENABLE_BREATH = os.getenv("ENABLE_BREATH_OVERLAY", "false").lower() == "true"


# -------------------------------------------------------
# SAVE UTILITIES
# -------------------------------------------------------

def save_episode_metadata(episode_id, metadata):
    path = EPISODE_DIR / f"{episode_id}_meta.json"
    path.write_text(json.dumps(metadata, indent=2))
    return str(path)


def save_pending_script(episode_id, blocks):
    path = EPISODE_DIR / f"{episode_id}_preview.json"
    path.write_text(json.dumps(blocks, indent=2))
    return str(path)


# -------------------------------------------------------
# MAIN SCRIPT GENERATION (NO AUDIO)
# -------------------------------------------------------

def generate_episode_script(episode_id=None, skip_ingest=False):

    print("\n=== [EpisodeRunner v5.2] GENERATING SCRIPT ===")

    # -----------------------------
    # Load stories
    # -----------------------------
    if skip_ingest:
        print("[ER] Using cached stories")
        raw = json.load(open(f"{BASE_DIR}/data/rolling_stories.json"))
        stories = raw if isinstance(raw, list) else raw.get("rundown", [])
    else:
        print("[ER] Ingesting fresh stories…")
        stories = run_ingestion()

    if not stories:
        raise RuntimeError("No stories available")

    # -----------------------------
    # PD Engine (IMPORTANT FIX)
    # -----------------------------
    pd_out = pd_engine(stories)

    # pd_engine_v45 returns a LIST, not dict
    if isinstance(pd_out, list):
        mode = "NEWS"
        cap = min(len(pd_out), 10)
        used = stories[:cap]
    else:
        mode = pd_out.get("mode", "NEWS")
        cap  = pd_out.get("story_cap", 10)
        used = stories[:cap]

    episode_id = episode_id or f"ep_{uuid.uuid4().hex[:8]}"

    # -----------------------------
    # Build timeline
    # -----------------------------
    timeline = build_timeline(used, show_mode=mode)

    blocks       = timeline["blocks"]
    audio_blocks = timeline["audio_blocks"]
    runtime_sec  = timeline["estimated_runtime_sec"]

    print(f"[ER] Blocks: {len(blocks)} | Mode: {mode}")

    preview_file = save_pending_script(episode_id, blocks)

    save_episode_metadata(episode_id, {
        "episode_id": episode_id,
        "timestamp": time.time(),
        "mode": mode,
        "runtime_sec": runtime_sec,
        "audio": None,
        "video": None,
        "preview_file": preview_file,
    })

    return {
        "episode_id": episode_id,
        "mode": mode,
        "blocks": blocks,
        "audio_blocks": audio_blocks,
    }


# -------------------------------------------------------
# APPROVAL → AUDIO → STITCH → (VIDEO LATER)
# -------------------------------------------------------

def approve_and_render(episode_id, audio_blocks):

    print(f"\n=== [EpisodeRunner] APPROVED → {episode_id} ===")

    audio_blocks_path = AUDIO_DIR / episode_id
    audio_blocks_path.mkdir(parents=True, exist_ok=True)

    # -----------------------------
    # TTS
    # -----------------------------
    if ENABLE_TTS:
        print("[ER] Rendering TTS blocks…")
        render_audio_blocks(episode_id, audio_blocks)
    else:
        print("[ER] TTS disabled")

    # -----------------------------
    # STITCH FINAL AUDIO
    # -----------------------------
    final_audio = stitch_episode_audio(
        episode_id=episode_id,
        audio_blocks_dir=str(audio_blocks_path),
        output_dir=str(EPISODE_DIR),
        enable_breath=ENABLE_BREATH
    )

    # -----------------------------
    # VIDEO (future)
    # -----------------------------
    video_path = None
    if os.getenv("ENABLE_VIDEO_RENDER", "false") == "true":
        video_path = render_episode(audio_blocks, final_audio, episode_id)

    # -----------------------------
    # Update metadata
    # -----------------------------
    meta_path = EPISODE_DIR / f"{episode_id}_meta.json"
    meta = json.load(open(meta_path))
    meta["audio"] = final_audio
    meta["video"] = video_path
    meta_path.write_text(json.dumps(meta, indent=2))

    return {
        "episode_id": episode_id,
        "audio": final_audio,
        "video": video_path,
    }


# -------------------------------------------------------
# AUTONOMOUS LOOP
# -------------------------------------------------------

def autonomous_loop():
    print("\n=== ToknNews Autonomous Mode Enabled ===")
    while True:
        ep = generate_episode_script()
        approve_and_render(ep["episode_id"], ep["audio_blocks"])
        time.sleep(1200)


if __name__ == "__main__":
    if AUTO_MODE:
        autonomous_loop()
    else:
        print("EpisodeRunner v5.2 ready.")
