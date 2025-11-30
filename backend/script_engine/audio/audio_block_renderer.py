#!/usr/bin/env python3
"""
audio_block_renderer.py
TOKEN NEWS — Audio Block Renderer (GPT-first broadcast stack)

Takes timeline audio blocks and:
  1. Sends each block to ElevenLabs via tts_renderer
  2. Collects rendered MP3 files
  3. Hands them to mixer to produce final scene audio
"""

import os
import time
from script_engine.audio.tts_renderer import render_block
from script_engine.audio.mixer import mix_scene


# =====================================================================
# MAIN FUNCTION: render all audio blocks for a scene
# =====================================================================

def render_audio_blocks(scene_id: str, audio_blocks: list):
    """
    Render all audio_blocks into a list of MP3 files and mix them.

    audio_blocks format:
    [
        {
            "speaker": "chip",
            "voice_id": "teAyVVX...",
            "text": "Welcome to Token News...",
            "block_type": "chip_intro",
            "timestamp": 1700000000.12345
        },
        ...
    ]
    """

    rendered_paths = []

    for block in audio_blocks:
        try:
            # Render using ElevenLabs
            mp3_path = render_block(block, scene_id)

            if mp3_path:
                rendered_paths.append(mp3_path)
            else:
                print(f"[AudioRenderer] WARNING: No audio rendered for block: {block}")

        except Exception as e:
            print("[AudioRenderer] ERROR during block rendering:", e)

    # If nothing rendered, return None safely
    if not rendered_paths:
        print("[AudioRenderer] No blocks rendered. Scene skipped.")
        return None

    # Mix everything into a final audio track
    try:
        final_audio_path = mix_scene(scene_id, rendered_paths)
        print(f"[AudioRenderer] Final audio mixed: {final_audio_path}")
        return final_audio_path

    except Exception as e:
        print("[AudioRenderer] MIX ERROR:", e)
        return None


# =====================================================================
# TEST MODE
# =====================================================================

if __name__ == "__main__":
    # Test blob for local debugging
    test_blocks = [
        {
            "speaker": "chip",
            "voice_id": "teAyVVX8spybXkITa1A0",
            "text": "This is a test line from Chip.",
            "block_type": "chip_test",
            "timestamp": time.time()
        },
        {
            "speaker": "vega",
            "voice_id": "Ax1HxHll9ku8pGyIt6kK",
            "text": "This is Vega checking audio pipeline.",
            "block_type": "vega_test",
            "timestamp": time.time()
        }
    ]

    print("[AudioRenderer] Running test render...")
    output = render_audio_blocks("test_scene", test_blocks)
    print("Final audio:", output)
