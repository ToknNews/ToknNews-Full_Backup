#!/usr/bin/env python3

"""
run_episode_no_audio.py
TOKN NEWS — No-Audio Episode Generator (2025 PDv3)

Runs:
 - PDv3
 - Dynamic Rundown
 - GPT Conversation Engine
 - Full timeline_builder_v3
But skips audio rendering entirely.
"""

import argparse
import json
import os
import sys
import time

# Ensure backend on path
BASE_DIR = "/opt/toknnews"
sys.path.insert(0, BASE_DIR)
sys.path.insert(0, f"{BASE_DIR}/backend")

from backend.script_engine.episode_runner import run_episode

# ============================================================
# CLI
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ToknNews — No Audio Episode Generator")
    parser.add_argument("--episode-id", type=str, default=None)
    parser.add_argument("--skip-ingest", action="store_true")
    parser.add_argument("--skip-audio", action="store_true", default=True)

    args = parser.parse_args()

    print("\n========== TOKN NEWS — EPISODE SCRIPT TEST (NO AUDIO) ==========\n")

    result = run_episode(
        episode_id=args.episode_id,
        skip_ingest=args.skip_ingest,
        skip_audio=True,           # always no audio
        daypart="evening",
        show_mode="NEWS",
        voice_map=None
    )

    if not result:
        print("ERROR: Episode generation failed.")
        sys.exit(1)

    blocks = result["blocks"]

    print("\n========== GENERATED SCRIPT BLOCKS ==========\n")

    for b in blocks:
        speaker = b["speaker"].upper()
        tag = b["tag"]
        text = b["text"]
        print(f"[{tag}] {speaker}: {text}")

    print("\n========================================================")
    print("Episode complete. Blocks saved to:")
    print(f" → {result['blocks_file']}")
    print("========================================================\n")

