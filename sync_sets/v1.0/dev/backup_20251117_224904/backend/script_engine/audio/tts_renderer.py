#!/usr/bin/env python3
"""
TOKNNews — ElevenLabs TTS Renderer (Final, Correct Version)
Produces valid MP3 audio files.
"""

import os, time, requests

AUDIO_DIR = "/var/www/toknnews/data/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

def render_block(block, scene_id):
    voice_id = block["voice_id"]
    text = block["text"]

    # Save as MP3, NOT WAV
    out_path = f"{AUDIO_DIR}/{scene_id}_{block['block_type']}_{int(block['timestamp'])}.mp3"

    if not ELEVEN_API_KEY:
        print("[Audio] Missing ELEVEN_API_KEY")
        return None

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
            "stability": 0.55,
            "similarity_boost": 0.65
        }
    }

    r = requests.post(url, headers=headers, json=payload)

    if r.status_code != 200:
        print("[Audio] ElevenLabs error:", r.text)
        return None

    if "audio" not in r.headers.get("Content-Type", ""):
        print("[Audio] Invalid audio response:", r.text)
        return None

    with open(out_path, "wb") as f:
        f.write(r.content)

    return out_path
