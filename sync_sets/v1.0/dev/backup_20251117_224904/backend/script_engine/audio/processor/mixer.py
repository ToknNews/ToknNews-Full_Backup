#!/usr/bin/env python3
"""
ToknNews Mixer Engine
- Takes rendered audio block list
- Applies processing
- Stitches into one clean broadcast WAV
"""

import os
from datetime import datetime
from pydub import AudioSegment
from .audio_utils import (
    load_audio, trim_silence, light_compression,
    hybrid_eq, normalize_lufs, apply_news_bed
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MIX_DIR = os.path.join(os.path.dirname(BASE_DIR), "mix")

os.makedirs(MIX_DIR, exist_ok=True)


def mix_audio_blocks(audio_list, news_bed=None):
    """
    audio_list = list of dicts:
      [{ "audio_file": "path.wav", "speaker": "...", "text": "...", ... }]

    Returns path to master broadcast WAV.
    """
    combined = AudioSegment.silent(duration=300)

    for entry in audio_list:
        wav = load_audio(entry["audio_file"])

        # Process chain
        wav = trim_silence(wav)
        wav = light_compression(wav)
        wav = hybrid_eq(wav)
        wav = normalize_lufs(wav, target_lufs=-17.0)
        wav = apply_news_bed(wav, bed_path=news_bed)

        # Stitch
        combined += wav + AudioSegment.silent(duration=150)

    # Final limiter
    combined = normalize_lufs(combined, target_lufs=-17.5)

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(MIX_DIR, f"mix_{ts}.wav")

    combined.export(out_path, format="wav")

    return out_path
