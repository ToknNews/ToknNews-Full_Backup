#!/usr/bin/env python3
"""
generate_vtt.py

Generate WebVTT captions from episode script JSON.
"""

import json
from pathlib import Path
import subprocess

EPISODES_DIR = Path("/var/www/toknnews/episodes")
VIDEO_DIR    = Path("/var/www/toknnews/data/video")

def get_video_duration(video_path: Path) -> float:
    """Return video duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(video_path)
    ]
    result = subprocess.check_output(cmd).decode().strip()
    return float(result)

def seconds_to_timestamp(sec: float) -> str:
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = sec % 60
    return f"{h:02}:{m:02}:{s:06.3f}".replace(".", ",")

def generate_vtt(episode_id: str):
    script_path = EPISODES_DIR / f"{episode_id}_script.json"
    video_path  = VIDEO_DIR / f"{episode_id}.mp4"
    out_path    = EPISODES_DIR / f"{episode_id}.vtt"

    if not script_path.exists() or not video_path.exists():
        print(f"[VTT] Missing files for {episode_id}")
        return

    script = json.loads(script_path.read_text())
    duration = get_video_duration(video_path)

    lines = []
    per_line = duration / max(len(script), 1)

    current = 0.0
    index = 1

    for block in script:
        start = current
        end = min(start + per_line, duration)
        speaker = block.get("speaker", "").upper()
        text = block.get("text", "").strip()

        lines.append(
            f"{index}\n"
            f"{seconds_to_timestamp(start)} --> {seconds_to_timestamp(end)}\n"
            f"{speaker}: {text}\n"
        )

        current = end
        index += 1

    vtt = "WEBVTT\n\n" + "\n".join(lines)
    out_path.write_text(vtt)
    print(f"[VTT] Generated {out_path}")

def main():
    for script_file in EPISODES_DIR.glob("ep_*_script.json"):
        episode_id = script_file.stem.replace("_script", "")
        generate_vtt(episode_id)

if __name__ == "__main__":
    main()
