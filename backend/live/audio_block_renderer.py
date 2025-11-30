#!/usr/bin/env python3
"""
TOKNNews — Audio Block Renderer (LIVE FINAL)
All audio generation is routed through the tokn-audio service.
"""

import requests

AUDIO_SERVER = "http://localhost:8999/render_scene"

def render_audio_blocks(scene_id, audio_blocks):
    payload = {
        "scene_id": scene_id,
        "audio_blocks": audio_blocks
    }

    try:
        r = requests.post(AUDIO_SERVER, json=payload)
        data = r.json()
    except Exception as e:
        print("[Audio] Exception:", e)
        return None

    if data.get("status") == "ok":
        return data.get("final_audio")

    print("[Audio] Error:", data)
    return None
