import requests
import json
import time

def render_audio_blocks(host, port, scene_id, audio_blocks):
    """
    Sends audio blocks to the local audio server (TTS + mixer).
    The server handles: tts_renderer → mixer → returns final file path.
    """
    url = f"http://{host}:{port}/render_scene"

    payload = {
        "scene_id": scene_id,
        "audio_blocks": audio_blocks
    }

    try:
        response = requests.post(url, json=payload, timeout=300)
        response.raise_for_status()
        data = response.json()

        if "final_path" not in data:
            print("[AudioBlockRenderer] ERROR: Missing final_path in server response")
            return None

        return data["final_path"]

    except Exception as e:
        print(f"[AudioBlockRenderer] ERROR sending audio blocks: {e}")
        return None
