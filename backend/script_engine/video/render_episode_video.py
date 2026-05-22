#!/usr/bin/env python3
"""
render_episode_video.py
ToknNews — Episode Video Render Wrapper (CANONICAL)

Contract:
- render_episode_video(episode_id: str) -> str
- Reads  /var/www/toknnews/data/audio/ep_<episode_id>_final.mp3
- Writes /var/www/toknnews/data/video/ep_<episode_id>.mp4
- Returns absolute mp4 path
"""

import subprocess
from pathlib import Path

# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR  = Path("/opt/toknnews")
AUDIO_DIR = Path("/var/www/toknnews/data/audio")
VIDEO_DIR = Path("/var/www/toknnews/data/video")

VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------
# MAIN RENDER
# --------------------------------------------------

def render_episode_video(episode_id: str) -> str:
    audio_path = AUDIO_DIR / f"ep_{episode_id}_final.mp3"
    if not audio_path.exists():
        raise FileNotFoundError(f"Missing audio: {audio_path}")

    # video_renderer.py expects ep_latest.mp3
    ep_latest = AUDIO_DIR / "ep_latest.mp3"
    subprocess.run(
        ["ln", "-sf", str(audio_path), str(ep_latest)],
        check=True
    )

    subprocess.run(
        [
            "python3",
            "backend/script_engine/video/video_renderer.py",
            episode_id,
        ],
        cwd=str(BASE_DIR),
        check=True
    )

    out_mp4 = VIDEO_DIR / f"ep_{episode_id}.mp4"
    if not out_mp4.exists():
        raise RuntimeError(
            f"Video render completed but output missing: {out_mp4}"
        )

    return str(out_mp4)

# --------------------------------------------------
# CLI
# --------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Usage: render_episode_video.py <episode_id>")

    print(render_episode_video(sys.argv[1]))
