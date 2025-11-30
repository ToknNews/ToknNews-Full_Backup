#!/usr/bin/env python3
"""
ToknNews LIVE — Old Audio Engine Redirect
All audio generation now routed to tokn-audio service.
"""

import requests

AUDIO_SERVER = "http://localhost:8999/render_scene"

def synthesize_line(text, voice_id, scene_id, block_type, timestamp):
    payload = {
        "scene_id": scene_id,
        "audio_blocks": [
            {
                "character": voice_id,
                "voice_id": voice_id,
                "block_type": block_type,
                "text": text,
                "timestamp": timestamp
            }
        ]
    }

    r = requests.post(AUDIO_SERVER, json=payload)
    try:
        data = r.json()
    except:
        print("[Audio Redirect] Bad JSON from audio server:", r.text)
        return None

    if data.get("status") == "ok":
        return data.get("final_audio")

    print("[Audio Redirect] Error:", data)
    return None
