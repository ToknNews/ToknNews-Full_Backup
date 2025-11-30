#!/usr/bin/env python3
"""
tts_renderer.py
TOKEN NEWS — ElevenLabs TTS Renderer (Modern + Stable)

This module:
 - Sends per-line text to ElevenLabs
 - Uses persona voice_id from voice_map
 - Saves MP3 files into '/opt/toknnews/data/audio'
 - Returns clean audio paths for mixer
"""

import os
import time
import requests

AUDIO_DIR = "/opt/toknnews/data/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
if not ELEVEN_API_KEY:
    print("[TTS] WARNING: ELEVEN_API_KEY not set — audio output will fail.")


# =====================================================================
# CORE TTS RENDERER
# =====================================================================

def render_block(block: dict, scene_id: str):
    """
    block = {
        "speaker": "chip",
        "voice_id": "...",
        "text": "Hello world",
        "block_type": "chip_intro",
        "timestamp": <float>
    }
    """

    voice_id = block.get("voice_id")
    text = block.get("text")

    if not text or not voice_id:
        print("[TTS] Invalid block:", block)
        return None

    # Build output path
    ts = int(time.time() * 1000)
    out_path = f"{AUDIO_DIR}/{scene_id}_{block['speaker']}_{block['block_type']}_{ts}.mp3"

    # ElevenLabs API v1 endpoint
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }

    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.65
        }
    }

    try:
        r = requests.post(url, headers=headers, json=payload)

        if r.status_code != 200:
            print("[TTS] ElevenLabs Error:", r.text)
            return None

        content_type = r.headers.get("Content-Type", "")
        if "audio" not in content_type:
            print("[TTS] Invalid response:", content_type)
            print("[TTS] Body:", r.text)
            return None

        # Write MP3
        with open(out_path, "wb") as f:
            f.write(r.content)

        return out_path

    except Exception as e:
        print("[TTS] Exception:", e)
        return None


# =====================================================================
# TEST MODE
# =====================================================================

if __name__ == "__main__":
    test_block = {
        "speaker": "chip",
        "voice_id": "teAyVVX8spybXkITa1A0",
        "text": "This is a test of the Token News audio pipeline.",
        "block_type": "test",
        "timestamp": time.time()
    }

    print("[TTS] Running test...")
    output = render_block(test_block, "debug_scene")
    print("Output:", output)
