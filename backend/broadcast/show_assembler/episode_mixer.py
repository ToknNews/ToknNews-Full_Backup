#!/usr/bin/env python3
"""
ToknNews Episode Mixer v1
Combines all segment_mix WAV files into a full-show master WAV.
"""

import os
from datetime import datetime
from pydub import AudioSegment

def build_episode_mix(show_dir):
    """
    Input: show_dir (folder containing segment_mix WAVs)
    Output: path to master show WAV
    """

    # find all segment mixes in order
    mixes = sorted(
        [f for f in os.listdir(show_dir) if f.endswith(".wav")],
        key=lambda x: os.path.getmtime(os.path.join(show_dir, x))
    )

    if not mixes:
        return None

    # 1. Intro music bed
    intro = AudioSegment.silent(duration=400)
    episode = intro

    # 2. Append each segment with smooth transitions
    for i, mix in enumerate(mixes):
        seg_path = os.path.join(show_dir, mix)
        seg_audio = AudioSegment.from_wav(seg_path)

        # 150ms crossfade between segments
        episode = episode.append(seg_audio, crossfade=150)

    # 3. Outro bed
    outro = AudioSegment.silent(duration=300)
    episode = episode.append(outro, crossfade=100)

    # 4. Save master mix
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    out_path = os.path.join(show_dir, f"episode_master_mix_{ts}.wav")
    episode.export(out_path, format="wav")

    return out_path
