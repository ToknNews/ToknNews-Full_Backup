import os
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv
load_dotenv("/opt/toknnews/.env")

ENABLE_TTS = os.environ.get("ENABLE_TTS", "false").lower() == "true"

client = ElevenLabs(api_key=os.environ.get("ELEVENLABS_API_KEY"))

def render_block(block, scene_id):
    if not ENABLE_TTS:
        print("[TTS Renderer] Skipping TTS — disabled via env var")
        return None

    voice_id = block.get("voice_id")
    text = block.get("text")

    if not voice_id or not text:
        print("[TTS Renderer] Missing voice_id or text")
        return None

    out_dir = f"/opt/toknnews/data/audio_blocks/{scene_id}"
    os.makedirs(out_dir, exist_ok=True)

    out_path = os.path.join(
        out_dir,
        f"{block['speaker']}_{int(block.get('timestamp', 0))}.mp3"
    )

    audio_stream = client.text_to_speech.convert(
        voice_id=voice_id,
        text=text,
        model_id="eleven_monolingual_v1"
    )

    with open(out_path, "wb") as f:
        for chunk in audio_stream:
            if chunk:
                f.write(chunk)

    return out_path
