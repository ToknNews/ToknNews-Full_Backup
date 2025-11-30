#!/usr/bin/env python3
"""
render_controller.py
TOKEN NEWS — Unified Render Orchestrator

Coordinates final MP4 generation using:
 - CapCut XML auto renderer (fast path)
 - Unreal Engine 5 render pipeline (pro path)

Inputs:
 - final audio file
 - blocks (timeline)
 - overlay metadata
 - episode metadata

Outputs:
 - final_episode_<id>.mp4
 - logs + intermediate files
"""

import os
import json
import subprocess
import time


BASE_DIR = "/opt/toknnews"
OUTPUT_DIR = f"{BASE_DIR}/output"
CAPCUT_DIR = f"{BASE_DIR}/render_capcut"
UNREAL_DIR = f"{BASE_DIR}/render_unreal"

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CAPCUT_DIR, exist_ok=True)
os.makedirs(UNREAL_DIR, exist_ok=True)


# ============================================================
# CAPCUT RENDERER (AUTO MODE)
# ============================================================

def build_capcut_project(blocks, audio_file, episode_id):
    """
    Creates a CapCut-compatible CCproj JSON to apply:
      - lower thirds
      - tickers
      - splash animations
      - clip overlays
      - audio track alignment
    """

    project = {
        "project_id": episode_id,
        "audio_file": audio_file,
        "tracks": [],
        "overlays": []
    }

    timestamp = 0.0
    for block in blocks:
        # Simple linear playback for now
        duration = 4.0  # safe estimate until we have real TTS durations

        overlay = block.get("visual_overlay", {})

        project["overlays"].append({
            "timestamp": timestamp,
            "duration": duration,
            "speaker": block["speaker"],
            "lower_third": overlay.get("lower_third"),
            "ticker": overlay.get("ticker"),
            "headline": overlay.get("headline"),
            "category": overlay.get("category"),
            "colors": overlay.get("color_theme"),
        })

        timestamp += duration

    # Save project file
    path = f"{CAPCUT_DIR}/{episode_id}.json"
    with open(path, "w") as f:
        json.dump(project, f, indent=2)

    return path


def render_capcut_to_mp4(capcut_json, output_path):
    """
    Uses FFmpeg to stitch MP4 from CapCut JSON.
    For now, this is a stub that produces a blank video with audio.
    """

    # Placeholder “blank video” generator
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "color=c=black:s=1920x1080:d=1200",
        "-i", capcut_json.replace(".json", ".mp3"),
        "-shortest",
        "-c:v", "libx264",
        "-c:a", "aac",
        output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        return True
    except Exception as e:
        print("[Render] ERROR generating video:", e)
        return False


# ============================================================
# UNREAL RENDERER (PRO MODE) — STUB FOR FUTURE EXPANSION
# ============================================================

def build_unreal_render_package(blocks, audio_file, episode_id):
    """
    Prepares Unreal Engine metadata folder:
      - timeline.json
      - audio reference
      - overlay metadata
      - block sequences for camera switching
    """

    pkg_dir = f"{UNREAL_DIR}/{episode_id}"
    os.makedirs(pkg_dir, exist_ok=True)

    data = {
        "episode_id": episode_id,
        "audio_file": audio_file,
        "timeline": blocks
    }

    with open(f"{pkg_dir}/timeline.json", "w") as f:
        json.dump(data, f, indent=2)

    return pkg_dir


# ============================================================
# RENDER COORDINATOR
# ============================================================

def render_episode(blocks, audio_file, episode_id, mode="capcut"):
    """
    mode = "capcut"  -> auto-render
    mode = "unreal"  -> generate UE5 folder
    """

    print(f"\n[RenderController] Rendering episode {episode_id} using mode: {mode}")

    if mode == "capcut":
        project_json = build_capcut_project(blocks, audio_file, episode_id)
        output_mp4  = f"{OUTPUT_DIR}/{episode_id}.mp4"

        ok = render_capcut_to_mp4(project_json, output_mp4)
        if ok:
            print(f"[RenderController] Render complete → {output_mp4}")
            return output_mp4
        else:
            print("[RenderController] CapCut render failed.")
            return None

    elif mode == "unreal":
        pkg = build_unreal_render_package(blocks, audio_file, episode_id)
        print(f"[RenderController] Unreal metadata package ready → {pkg}")
        return pkg

    else:
        print("[RenderController] Unknown mode:", mode)
        return None
