#!/usr/bin/env python3
from render_controller import render_episode
import json, os

# Render last episode for testing
BASE_DIR = "/opt/toknnews"
BLOCKS_PATH = f"{BASE_DIR}/output/last_blocks.json"
AUDIO_PATH  = f"{BASE_DIR}/output/last_audio.mp3"

if __name__ == "__main__":
    if not os.path.exists(BLOCKS_PATH) or not os.path.exists(AUDIO_PATH):
        print("[RenderPM2] Nothing to render yet.")
    else:
        with open(BLOCKS_PATH, "r") as f:
            blocks = json.load(f)
        print(render_episode(blocks, AUDIO_PATH, "manual_test", mode="capcut"))
