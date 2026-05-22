#!/usr/bin/env python3
"""
promo_audio_renderer.py — Promo TTS renderer (ElevenLabs)

Contract:
- render_promo_audio(anchor: str, text: str, render_id: str) -> str
- Writes /var/www/toknnews/data/audio/<render_id>_final.mp3
"""

from __future__ import annotations
import os
import shutil
from pathlib import Path
from dotenv import load_dotenv

from script_engine.audio.tts_renderer import render_block
from script_engine.audio.mixer import mix_scene

load_dotenv("/opt/toknnews/.env")

VOICE_MAP = {
    "chip":   os.getenv("VOICE_CHIP"),
    "vega":   os.getenv("VOICE_VEGA"),
    "cash":   os.getenv("VOICE_CASH"),
    "ledger": os.getenv("VOICE_LEDGER"),
    "reef":   os.getenv("VOICE_REEF"),
    "bond":   os.getenv("VOICE_BOND"),
    "lawson": os.getenv("VOICE_LAWSON"),
    "ivy":    os.getenv("VOICE_IVY"),
    "bitsy":  os.getenv("VOICE_BITSY"),
    "penny":  os.getenv("VOICE_PENNY"),
    "neura":  os.getenv("VOICE_NEURA"),
    "cap":    os.getenv("VOICE_CAP"),
    "rex":    os.getenv("VOICE_REX"),
}

AUDIO_DIR = Path("/var/www/toknnews/data/audio")
AUDIO_DIR.mkdir(parents=True, exist_ok=True)


def render_promo_audio(anchor: str, text: str, render_id: str) -> str:
    anchor = (anchor or "chip").strip().lower()
    text = (text or "").strip()

    if not render_id or not text:
        raise RuntimeError("render_id and text required")

    voice_id = VOICE_MAP.get(anchor)
    if not voice_id:
        raise RuntimeError(f"No ElevenLabs voice mapped for anchor '{anchor}'")

    block_id = f"{render_id}_000"
    payload = {
        "speaker": anchor,
        "voice_id": voice_id,
        "text": text,
        "block_type": "promo",
    }

    mp3_path = render_block(payload, block_id)
    if not mp3_path or not os.path.exists(mp3_path):
        raise RuntimeError("TTS render_block failed")

    mixed_path = mix_scene(render_id, [mp3_path])
    if not mixed_path or not os.path.exists(mixed_path):
        raise RuntimeError("mix_scene failed for promo audio")

    final_audio = AUDIO_DIR / f"{render_id}_final.mp3"

    # If mixer already wrote canonical, do nothing
    if os.path.abspath(str(mixed_path)) != os.path.abspath(str(final_audio)):
        shutil.copyfile(mixed_path, final_audio)

    return str(final_audio)
