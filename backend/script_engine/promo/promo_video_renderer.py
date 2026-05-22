#!/usr/bin/env python3
"""
promo_video_renderer.py — Promo Renderer (Uses Episode Renderer in Portrait Mode)
"""

from __future__ import annotations
import uuid
import shutil
from pathlib import Path

from backend.script_engine.video.video_renderer import render_episode_video

AUDIO_DIR = Path("/var/www/toknnews/data/audio")
VIDEO_DIR = Path("/var/www/toknnews/data/video")

AUDIO_DIR.mkdir(parents=True, exist_ok=True)
VIDEO_DIR.mkdir(parents=True, exist_ok=True)


def render_promo_video(render_id: str, audio_mp3_path: str) -> str:

    audio = Path(audio_mp3_path)
    if not audio.exists():
        raise FileNotFoundError(f"Missing promo audio: {audio}")

    ep_latest = AUDIO_DIR / "ep_latest.mp3"

    if ep_latest.exists() or ep_latest.is_symlink():
        ep_latest.unlink()

    ep_latest.symlink_to(audio.resolve())

    temp_episode_id = f"promo_tmp_{uuid.uuid4().hex[:8]}"

    # Force portrait mode
    rendered_path = render_episode_video(temp_episode_id, mode="portrait")

    rendered_file = Path(rendered_path)
    if not rendered_file.exists():
        raise RuntimeError("Episode renderer did not produce output")

    final_path = VIDEO_DIR / f"{render_id}.mp4"

    if final_path.exists():
        final_path.unlink()

    shutil.move(str(rendered_file), str(final_path))

    if ep_latest.exists():
        ep_latest.unlink()

    return str(final_path)
