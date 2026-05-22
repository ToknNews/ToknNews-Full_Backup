#!/usr/bin/env python3
"""
episode_runner.py — Delegation Wrapper (Intelligence Platform Mode v3)

Ensures preview file matches legacy naming:
ep_<episode_id>_preview.json
"""

import json
import time
import shutil
from pathlib import Path
from typing import Dict, Any

BASE_DIR = "/opt/toknnews"
EPISODE_DIR = Path(f"{BASE_DIR}/data/episodes")
EPISODE_DIR.mkdir(parents=True, exist_ok=True)


def generate_episode_script(
    *,
    episode_id: str | None = None,
    skip_ingest: bool = False
) -> Dict[str, Any]:

    print("\n=== [EpisodeRunner] Delegating to Intelligence Runner ===")

    from backend.script_engine.intelligence_runner import run_intelligence

    result = run_intelligence(skip_ingest=skip_ingest)

    source_preview_path = Path(result["preview"])

    if not source_preview_path.exists():
        raise RuntimeError("Preview file not found after intelligence run")

    episode_id = episode_id or result["run_id"]

    # 🔥 COPY to legacy-compatible filename
    legacy_preview_path = EPISODE_DIR / f"ep_{episode_id}_preview.json"
    shutil.copyfile(source_preview_path, legacy_preview_path)

    timeline = json.loads(legacy_preview_path.read_text())

    runtime_sec = sum(int(b.get("runtime_sec", 30)) for b in timeline)

    meta = {
        "episode_id": episode_id,
        "title": f"ToknNews {episode_id}",
        "timestamp": time.time(),
        "mode": "NEWS",
        "runtime_sec": runtime_sec,
        "status": "preview",
        "preview_file": str(legacy_preview_path),
    }

    (EPISODE_DIR / f"ep_{episode_id}_meta.json").write_text(
        json.dumps(meta, indent=2)
    )

    return {
        "episode_id": episode_id,
        "title": meta["title"],
        "blocks": timeline,
        "runtime_sec": runtime_sec,
        "preview_file": str(legacy_preview_path),
    }


def approve_and_render(episode_id: str) -> Dict[str, str]:
    from backend.script_engine.audio.audio_block_renderer import render_episode_audio
    from backend.script_engine.video.render_episode_video import render_episode_video

    audio_path = render_episode_audio()
    if not audio_path:
        raise RuntimeError("Audio render failed")

    video_path = render_episode_video(episode_id)
    if not video_path:
        raise RuntimeError("Video render failed")

    return {
        "episode_id": episode_id,
        "audio": audio_path,
        "video": video_path,
    }


if __name__ == "__main__":
    print("EpisodeRunner delegating to intelligence_runner.")
