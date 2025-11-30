#!/usr/bin/env python3
"""
TOKNNews — Audio Block Renderer (Local Dev Server)
Used only for previewing audio via localhost:8999.
"""

import requests

AUDIO_SERVER = "http://localhost:8999/render_scene"

def render_audio_blocks(scene_id, audio_blocks):
    payload = {
        "scene_id": scene_id,
        "audio_blocks": audio_blocks
    }

    r = requests.post(AUDIO_SERVER, json=payload)
    try:
        data = r.json()
    except:
        return None

    if data.get("status") == "ok":
        return data.get("final_audio")

    print("[Audio] Error via audio_block_renderer:", data)
    return None
