#!/usr/bin/env python3
"""
audio_block_renderer.py
TOKEN NEWS — Audio Block Renderer (PRODUCTION CANON v2 FIXED)

Fix:
- Normalizes speaker names to lowercase before voice lookup
- Prevents uppercase preview JSON from breaking TTS
"""

import os
import argparse
from pathlib import Path
from dotenv import load_dotenv

from script_engine.audio.tts_renderer import render_block
from script_engine.audio.mixer import mix_scene
from script_engine.editorial.timeline_loader import load_episode_audio_blocks

# -----------------------------------------------------
# ENV
# -----------------------------------------------------

load_dotenv("/opt/toknnews/.env")

VOICE_MAP = {
    "chip":   os.getenv("VOICE_CHIP"),
    "vega":   os.getenv("VOICE_VEGA"),
    "cash":   os.getenv("VOICE_CASH"),
    "ledger": os.getenv("VOICE_LEDGER"),
    "reef":   os.getenv("VOICE_REEF"),
    "bond":   os.getenv("VOICE_BOND"),
    "lawson": os.getenv("VOICE_LAWSON"),
    "ivy":    os.getenv("VOICE_IVY"),
    "bitsy":  os.getenv("VOICE_BITSY"),
    "penny":  os.getenv("VOICE_PENNY"),
    "neura":  os.getenv("VOICE_NEURA"),
    "cap":    os.getenv("VOICE_CAP"),
    "rex":    os.getenv("VOICE_REX"),
}

AUDIO_DIR = Path("/var/www/toknnews/data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


# -----------------------------------------------------
# CORE RENDERER
# -----------------------------------------------------

def render_episode_audio():

    episode_id, audio_blocks = load_episode_audio_blocks()

    if not episode_id or not audio_blocks:
        raise RuntimeError("Invalid episode data from timeline_loader")

    rendered_paths = []

    for idx, block in enumerate(audio_blocks):

        speaker_raw = block.get("speaker")
        text = block.get("text")

        if not speaker_raw or not text:
            continue

        speaker = speaker_raw.lower()  # 🔥 FIX: normalize case

        voice_id = VOICE_MAP.get(speaker)
        if not voice_id:
            print(f"[AudioRenderer] No voice mapped for '{speaker_raw}', skipping")
            continue

        block_id = f"ep_{episode_id}_{idx:03d}"

        payload = {
            "speaker": speaker,
            "voice_id": voice_id,
            "text": text,
            "block_type": block.get("block_type", "dialogue"),
        }

        mp3_path = render_block(payload, block_id)
        if mp3_path:
            rendered_paths.append(mp3_path)

    if not rendered_paths:
        raise RuntimeError("No audio blocks rendered — aborting")

    final_audio_path = mix_scene(
        f"ep_{episode_id}",
        rendered_paths
    )

    print(f"[AudioRenderer] Final audio written → {final_audio_path}")
    return final_audio_path


# -----------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--episode",
        action="store_true",
        help="Render full episode audio from latest preview"
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.episode:
        render_episode_audio()
    else:
        print("[AudioRenderer] No action specified. Use --episode")
