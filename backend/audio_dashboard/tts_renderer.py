import os
import time
import requests

ELEVEN_API_KEY = os.environ.get("ELEVENLABS_API_KEY")

TTS_ENDPOINT = "https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"


def render_block(block, scene_id):
    """
    Renders a single TTS audio block using ElevenLabs.
    block = {
        "character": "...",
        "voice_id": "...",
        "text": "...",
        "block_type": "...",
        "timestamp": ...
    }
    Returns path to saved .mp3 file or None on failure.
    """

    voice_id = block.get("voice_id")
    text     = block.get("text")
    ts       = int(time.time())

    if not voice_id or not text:
        print(f"[TTS] ERROR: Missing voice_id or text in block: {block}")
        return None

    if not ELEVEN_API_KEY:
        print("[TTS] ERROR: ELEVENLABS_API_KEY missing")
        return None

    url = TTS_ENDPOINT.format(voice_id=voice_id)

    headers = {
        "xi-api-key": ELEVEN_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "text": text,
        "model_id": "eleven_multilingual_v2",
        "voice_settings": {
            "stability": 0.35,
            "similarity_boost": 0.85
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload, stream=True, timeout=60)
        response.raise_for_status()

        out_dir = "tts_blocks"
        os.makedirs(out_dir, exist_ok=True)

        file_path = os.path.join(out_dir, f"{scene_id}_{voice_id}_{ts}.mp3")

        with open(file_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    f.write(chunk)

        return file_path

    except Exception as e:
        print(f"[TTS] ERROR rendering block: {e}")
        return None
