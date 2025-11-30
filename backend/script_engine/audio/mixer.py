#!/usr/bin/env python3
"""
TOKNNews — Audio Mixer (Final Version)
Accepts MP3 or WAV automatically.
"""

import os
from pydub import AudioSegment

AUDIO_DIR = "/var/www/toknnews/data/audio"

def mix_scene(scene_id: str, mp3_paths: list):
    """
    Takes a list of MP3 file paths and produces one combined MP3 file.
    Inserts natural silence between blocks.
    """

    if not mp3_paths:
        print("[Mixer] No MP3 paths provided.")
        return None

    final_mix = AudioSegment.silent(duration=1)

    # Choose a silence window between 300–500 ms
    def natural_pause():
        return AudioSegment.silent(duration=random.randint(300, 500))

    for idx, p in enumerate(mp3_paths):
        seg = load_mp3(p)

        # Normalize segment
        try:
            seg = seg.apply_gain(-seg.max_dBFS)
        except Exception:
            pass

        # Add segment
        final_mix += seg

        # Add silence BETWEEN segments, not after the last one
        if idx < len(mp3_paths) - 1:
            final_mix += natural_pause()

    # Optional: Apply fade in/out
    final_mix = final_mix.fade_in(150).fade_out(200)

    # Export
    out_path = f"{AUDIO_DIR}/{scene_id}_final.mp3"
    final_mix.export(out_path, format="mp3")

    print(f"[Mixer] Scene mixed → {out_path}")
    return out_path
