#!/usr/bin/env python3
"""
TOKNNews — Audio Mixer (Final Version)
Accepts MP3 or WAV automatically.
"""

import os
from pydub import AudioSegment

AUDIO_DIR = "/var/www/toknnews/data/audio"

def mix_scene(scene_id, block_paths):
    final = AudioSegment.empty()

    for p in block_paths:
        seg = AudioSegment.from_file(p)  # auto-detect format
        final += seg

    out_path = f"{AUDIO_DIR}/{scene_id}_final.mp3"
    final.export(out_path, format="mp3")

    return out_path
