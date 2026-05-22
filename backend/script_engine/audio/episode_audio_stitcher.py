#!/usr/bin/env python3
"""
episode_audio_stitcher.py
Stitches ordered audio blocks into a single episode audio file
with optional post-render realism (breath overlay).
"""

import os
from pydub import AudioSegment

from backend.script_engine.audio.breath_overlay import maybe_add_breath


def stitch_episode_audio(
    episode_id,
    audio_blocks_dir,
    output_dir,
    *,
    enable_breath=False
):
    """
    audio_blocks_dir: folder with ordered wav/mp3 files
    output_dir: /opt/toknnews/data/episodes
    enable_breath: bool — subtle realism layer (post-render)
    """

    files = sorted(
        f for f in os.listdir(audio_blocks_dir)
        if f.endswith((".wav", ".mp3"))
    )

    if not files:
        raise RuntimeError("No audio blocks found to stitch")

    final = AudioSegment.empty()

    for f in files:
        path = os.path.join(audio_blocks_dir, f)
        final += AudioSegment.from_file(path)

    # -----------------------------------
    # OPTIONAL POST-RENDER REALISM
    # -----------------------------------
    final = maybe_add_breath(final, enable=enable_breath)

    os.makedirs(output_dir, exist_ok=True)
    out_path = os.path.join(output_dir, f"{episode_id}.mp3")
    final.export(out_path, format="mp3")

    return out_path
