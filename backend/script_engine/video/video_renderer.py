#!/usr/bin/env python3
"""
video_renderer.py
ToknNews — Episode Video Renderer (MODE-AWARE, DURATION-LOCKED)

Responsibilities:
- Lock video duration to audio length
- Render static background
- Overlay audio-driven waveform
- Support landscape (default) or portrait override
"""

import os
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# -----------------------------------------------------
# ENV
# -----------------------------------------------------

load_dotenv("/opt/toknnews/.env")

DEFAULT_VIDEO_MODE = os.getenv("VIDEO_MODE", "landscape").lower()
VIDEO_FPS = int(os.getenv("VIDEO_FPS", "30"))

# -----------------------------------------------------
# PATHS
# -----------------------------------------------------

BASE_DIR  = Path("/opt/toknnews")
AUDIO_DIR = Path("/var/www/toknnews/data/audio")
VIDEO_DIR = Path("/var/www/toknnews/data/video")
ASSET_DIR = BASE_DIR / "frontend/assets/img"

VIDEO_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------
# HELPERS
# -----------------------------------------------------

def _audio_duration_seconds(audio_path: Path) -> float:
    cmd = [
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(audio_path),
    ]
    return float(subprocess.check_output(cmd).decode().strip())

# -----------------------------------------------------
# CORE RENDER
# -----------------------------------------------------

def render_episode_video(episode_id: str, mode: str | None = None) -> str:

    # Determine mode
    mode = (mode or DEFAULT_VIDEO_MODE).lower()

    if mode == "portrait":
        VIDEO_WIDTH, VIDEO_HEIGHT = 1080, 1920
    else:
        VIDEO_WIDTH, VIDEO_HEIGHT = 1280, 720

    audio_path = AUDIO_DIR / "ep_latest.mp3"
    if not audio_path.exists():
        raise FileNotFoundError(f"Missing audio for render: {audio_path}")

    background = ASSET_DIR / "YT_Banner_Tokn.jpg"
    if not background.exists():
        raise FileNotFoundError(f"Missing background asset: {background}")

    out_mp4 = VIDEO_DIR / f"ep_{episode_id}.mp4"

    dur = _audio_duration_seconds(audio_path)
    dur = max(1.0, dur + 0.25)

    filter_complex = (
        f"[0:v]scale={VIDEO_WIDTH}:{VIDEO_HEIGHT}:"
        f"force_original_aspect_ratio=decrease,"
        f"pad={VIDEO_WIDTH}:{VIDEO_HEIGHT}:(ow-iw)/2:(oh-ih)/2,"
        f"format=yuv420p[bg];"
        f"[1:a]showwaves=s={VIDEO_WIDTH}x200:"
        f"mode=line:"
        f"colors=white@0.8[wave];"
        f"[bg][wave]overlay=0:H-h-40[vout]"
    )

    cmd = [
        "ffmpeg",
        "-y",

        "-loop", "1",
        "-i", str(background),
        "-i", str(audio_path),

        "-t", f"{dur:.3f}",

        "-filter_complex", filter_complex,

        "-r", str(VIDEO_FPS),

        "-map", "[vout]",
        "-map", "1:a:0",

        "-c:v", "libx264",
        "-preset", "veryfast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",

        "-c:a", "aac",
        "-b:a", "192k",

        "-shortest",

        str(out_mp4),
    ]

    print(
        f"[VideoRenderer] Rendering {episode_id} "
        f"mode={mode} {VIDEO_WIDTH}x{VIDEO_HEIGHT}@{VIDEO_FPS} "
        f"dur={dur:.2f}s"
    )

    subprocess.run(cmd, check=True)

    if not out_mp4.exists():
        raise RuntimeError(f"Video render failed: {out_mp4}")

    return str(out_mp4)


# -----------------------------------------------------
# CLI
# -----------------------------------------------------

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        raise SystemExit("Usage: video_renderer.py <episode_id>")
    print(render_episode_video(sys.argv[1]))
