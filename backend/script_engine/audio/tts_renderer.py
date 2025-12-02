import os

ENABLE_TTS = os.environ.get("ENABLE_TTS", "false").lower() == "true"

def render_block(*args, **kwargs):
    if not ENABLE_TTS:
        print("[TTS Renderer] Skipping TTS — disabled via env var")
        return "/dev/null"
    try:
        # Placeholder for ElevenLabs or actual TTS implementation
        print("[TTS Renderer] Rendering block via ElevenLabs (placeholder)")
        return "/tmp/fake_audio.mp3"
    except Exception as e:
        print(f"[TTS Renderer] ERROR: {e}")
        return None
