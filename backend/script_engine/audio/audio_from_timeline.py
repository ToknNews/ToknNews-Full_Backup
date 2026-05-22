#!/usr/bin/env python3
"""
audio_from_timeline.py

Purpose:
- Convert episode_timeline.json into ordered TTS audio blocks
- Preserve exact broadcast order
- Flatten dialogue turns correctly
"""

import json
import time
from pathlib import Path

from audio_block_renderer import render_audio_blocks

# -----------------------------------------------------
# PATHS
# -----------------------------------------------------

TIMELINE_PATH = Path("/opt/toknnews/data/episodes/episode_timeline.json")
VOICE_MAP_PATH = Path("/opt/toknnews/backend/script_engine/persona/voice_map.json")

VOICE_MAP = json.loads(VOICE_MAP_PATH.read_text())

# -----------------------------------------------------
# MAIN
# -----------------------------------------------------

def main():
    timeline = json.loads(TIMELINE_PATH.read_text())

    audio_blocks = []
    order = 0  # 🔒 absolute ordering index

    for item in timeline:
        block_type = item.get("type")

        # -----------------------------
        # MONOLOGUES & TRANSITIONS
        # -----------------------------
        if block_type in ("monologue", "transition"):
            speaker = item.get("speaker")
            text = item.get("text")

            if not speaker or not text:
                continue

            voice_id = VOICE_MAP.get(speaker)
            if not voice_id:
                print(f"[Audio] No voice for speaker '{speaker}', skipping")
                continue

            audio_blocks.append({
                "order": order,
                "speaker": speaker,
                "voice_id": voice_id,
                "text": text,
                "block_type": block_type,
                "timestamp": time.time()
            })
            order += 1

        # -----------------------------
        # DIALOGUE (FLATTEN TURNS)
        # -----------------------------
        elif block_type == "dialogue":
            for turn in item.get("turns", []):
                speaker = turn.get("speaker")
                text = turn.get("text")

                if not speaker or not text:
                    continue

                voice_id = VOICE_MAP.get(speaker)
                if not voice_id:
                    print(f"[Audio] No voice for speaker '{speaker}', skipping")
                    continue

                audio_blocks.append({
                    "order": order,
                    "speaker": speaker,
                    "voice_id": voice_id,
                    "text": text,
                    "block_type": "dialogue",
                    "timestamp": time.time()
                })
                order += 1

    # -------------------------------------------------
    # ENFORCE ORDER (CRITICAL)
    # -------------------------------------------------
    audio_blocks.sort(key=lambda x: x["order"])

    episode_id = f"ep_{int(time.time())}"
    print(f"[Audio] Rendering episode {episode_id} ({len(audio_blocks)} blocks)")

    render_audio_blocks(episode_id, audio_blocks)

# -----------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------

if __name__ == "__main__":
    main()
