#!/usr/bin/env python3
"""
breath_overlay.py
TOKEN NEWS — Optional Breath/Warmup Overlays

Used sparingly for realism.
"""

from pydub import AudioSegment
import random

# Placeholder for breath/warmup sounds
# You can add real samples later, e.g.:
# BREATH_SAMPLES = [AudioSegment.from_mp3("breath1.mp3"), ...]
BREATH_SAMPLES = []

def maybe_add_breath(segment: AudioSegment, enable=False) -> AudioSegment:
    """
    If enabled and samples exist, overlays a subtle breath sound.
    """
    if not enable or not BREATH_SAMPLES:
        return segment

    breath = random.choice(BREATH_SAMPLES)

    # Very subtle volume
    breath = breath - 18

    # Overlay at the beginning
    mixed = segment.overlay(breath, position=0)
    return mixed
