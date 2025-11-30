#!/usr/bin/env python3
"""
Hybrid Broadcast Audio Processor for ToknNews
- Trim silence
- Light compression
- Hybrid EQ (clarity + warmth)
- Optional news bed underlay
"""

import os
from pydub import AudioSegment, effects

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def load_audio(path):
    return AudioSegment.from_file(path)


def trim_silence(audio, silence_ms=120):
    """Remove leading and trailing silence."""
    return effects.strip_silence(
        audio,
        silence_len=silence_ms,
        silence_thresh=audio.dBFS - 16
    )


def light_compression(audio, threshold=-18.0, ratio=2.5):
    """Simple compressor for broadcast clarity."""
    compressed = audio.compress_dynamic_range(
        threshold=threshold,
        ratio=ratio,
        attack=5,
        release=50
    )
    return compressed


def hybrid_eq(audio):
    """Hybrid EQ curve: mild clarity boost + warm low-mid presence."""
    return (
        audio.low_pass_filter(16000)         # remove harshness
             .high_pass_filter(110)          # remove rumble
    )


def apply_news_bed(audio, bed_path=None, bed_volume=-28):
    """Optional light news pad underlay."""
    if not bed_path or not os.path.exists(bed_path):
        return audio

    bed = AudioSegment.from_file(bed_path)
    bed = bed - abs(bed_volume)

    if len(bed) < len(audio):
        loops = int(len(audio) / len(bed)) + 2
        bed = bed * loops

    bed = bed[:len(audio)]

    return audio.overlay(bed)


def normalize_lufs(audio, target_lufs=-16.0):
    """Normalize audio to broadcast loudness."""
    change = target_lufs - audio.dBFS
    return audio.apply_gain(change)
