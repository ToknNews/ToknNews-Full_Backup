#!/usr/bin/env python3
"""
TOKNNews — ElevenLabs TTS Renderer (Final, Correct Version)
Produces valid MP3 audio files.
"""

# ------------------------------------------------------------
# Standard Imports Only (TTS does NOT import persona modules)
# ------------------------------------------------------------
import os
import time
import requests

AUDIO_DIR = "/var/www/toknnews/data/audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")

# ------------------------------------------------------------
# TTS FILTER — ACRONYMS (PHONETIC) + EXPANSIONS (SEMANTIC)
# ------------------------------------------------------------

def apply_tts_filter(text: str) -> str:
    # --- Spoken expansions (semantic replacements) ---
    expand = {
        "TVL": "total value locked",
        "APR": "annual percentage rate",
        "APY": "annual percentage yield",
        "KYC": "know your customer",
        "AML": "anti money laundering",
    }

    # --- Phonetic corrections (crypto + finance acronyms) ---
    phonetic = {
        "ETH": "EETH",
        "BTC": "B T C",
        "USDC": "U S D C",
        "USDT": "U S D T",
        "CPI": "C P I",
        "PPI": "P P I",
        "FOMC": "F O M C",
        "GPU": "G P U",
        "TPU": "T P U",
        "LLM": "L L M",
        "API": "A P I",
        "MEV": "M E V",
        "AML": "A M L",
        "KYC": "K Y C",   # fallback if not expanded earlier
        "L1": "Layer 1",
        "L2": "Layer 2",
    }

    # --- Perform expansions first ---
    for k, v in expand.items():
        text = text.replace(k, v)

    # --- Then apply phonetic mappings ---
    for k, v in phonetic.items():
        text = text.replace(k, v)

    return text


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
        "text": apply_phonetic_filter(text),
        "model_id": "eleven_monolingual_v1",
        "voice_settings" = {
            "stability": 0.25,
            "similarity_boost": 0.95
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
