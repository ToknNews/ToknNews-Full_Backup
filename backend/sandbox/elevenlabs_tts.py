#!/usr/bin/env python3
import os, sys, json
from datetime import datetime
from elevenlabs import ElevenLabs
from metrics_logger import log_metric
raise SystemExit("sandbox/elevenlabs_tts.py disabled — using tokn-audio service")

GO_LIVE          = True
VOICE_MAP_PATH   = "/var/www/toknnews/devmodules/voice_map.json"
# === INPUT HANDLING ===
# Each voice/order gets its own text file:
#   /var/www/toknnews/devdata/audio_scripts/<order>_<voice_key>.txt
# Falls back to chip_latest.txt if that file doesn’t exist.
def get_input_path(order: str, voice_key: str) -> str:
    custom_path = f"/var/www/toknnews/devdata/audio_scripts/{order}_{voice_key}.txt"
    default_path = "/var/www/toknnews/devdata/audio_scripts/chip_latest.txt"
    return custom_path if os.path.exists(custom_path) else default_path
OUTPUT_AUDIO_DIR = "/var/www/toknnews/devdata/audio"
DEFAULT_VOICE    = "Chip_Standard"
DEFAULT_ORDER    = "00"
MODEL_ID         = "eleven_multilingual_v2"
OUTPUT_FORMAT    = "mp3_44100_128"
VOICE_SETTINGS   = {"stability":0.45, "similarity_boost":0.75, "style":0.40}

def die(msg): print(f"[Error] {msg}",flush=True); sys.exit(1)

def ensure_text(path):
    if not os.path.exists(path): die(f"Missing input: {path}")
    txt = open(path,"r").read().strip()
    if not txt: die("Input text file is empty.")
    return txt

def main():
    api = os.environ.get("ELEVEN_API_KEY") or die("ELEVEN_API_KEY not set")
    try:
        voices = json.load(open(VOICE_MAP_PATH))
    except Exception as e:
        die(f"Cannot load {VOICE_MAP_PATH}: {e}")

    voice_key = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_VOICE
    order_in  = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_ORDER
    if voice_key not in voices:
        die(f"Voice '{voice_key}' not in voice_map. Known: {', '.join(sorted(voices))}")

    try: order = f"{int(order_in):02d}"
    except:   order = DEFAULT_ORDER

    voice_id = voices[voice_key]
    INPUT_TXT_PATH = get_input_path(order, voice_key)
    text = ensure_text(INPUT_TXT_PATH)
    ts       = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(OUTPUT_AUDIO_DIR,f"{order}_{voice_key.lower()}_{ts}.mp3")

    print("\n=== ElevenLabs TTS ===")
    print(f" Voice  : {voice_key} ({voice_id})")
    print(f" Order  : {order}")
    print(f" Output : {out_path}")
    print(f" GO_LIVE: {GO_LIVE}")
    print("======================",flush=True)

    if not GO_LIVE:
        print("[Dry Run] Skipping API call.")
        return

    client = ElevenLabs(api_key=api)
    stream = client.text_to_speech.convert(
        voice_id=voice_id,
        model_id=MODEL_ID,
        text=text,
        output_format=OUTPUT_FORMAT,
        voice_settings=VOICE_SETTINGS
    )

    os.makedirs(OUTPUT_AUDIO_DIR,exist_ok=True)
    with open(out_path,"wb") as fh:
        for chunk in stream:
            if isinstance(chunk,(bytes,bytearray)): fh.write(chunk)

    print(f"[Success] {out_path}",flush=True)
    log_metric("tts_generation_success",voice_key,{"output":out_path})

if __name__=="__main__": main()
