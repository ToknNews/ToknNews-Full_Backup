#!/usr/bin/env python3
"""
publish_static_episodes.py

PURPOSE:
- Publish rendered episodes to static frontend
- NEVER regenerate titles
- NEVER touch unpublished episodes
- Deterministic, idempotent behavior
"""

import json
import os
from pathlib import Path
from string import Template

# -----------------------------------------------------
# PATHS
# -----------------------------------------------------

AUDIO_DIR   = Path("/var/www/toknnews/data/audio")
VIDEO_DIR   = Path("/var/www/toknnews/data/video")
EPISODE_DIR = Path("/opt/toknnews/data/episodes")

PUBLIC_EPISODES_DIR = Path("/var/www/toknnews/episodes")
TEMPLATE_PATH = Path("/opt/toknnews/backend/script_engine/episode_page_template.html")

PUBLIC_EPISODES_DIR.mkdir(parents=True, exist_ok=True)
PAGE_TEMPLATE = Template(TEMPLATE_PATH.read_text())

# -----------------------------------------------------
# HELPERS
# -----------------------------------------------------

def load_episode_meta(episode_id: str) -> dict | None:
    path = EPISODE_DIR / f"{episode_id}_meta.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


def load_episode_script(episode_id: str) -> list | None:
    """
    Script is frozen at preview time and stored per episode.
    """
    path = EPISODE_DIR / f"{episode_id}_preview.json"
    if not path.exists():
        return None
    return json.loads(path.read_text())


# -----------------------------------------------------
# MAIN
# -----------------------------------------------------

def main():
    index = []

    audio_files = sorted(
        AUDIO_DIR.glob("ep_*_final.mp3"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not audio_files:
        print("[Publisher] No audio files found.")
        return

    for audio_path in audio_files:
        episode_id = audio_path.stem.replace("_final", "")
        video_path = VIDEO_DIR / f"{episode_id}.mp4"

        # Only publish fully rendered episodes
        if not video_path.exists():
            continue

        meta = load_episode_meta(episode_id)
        if not meta:
            print(f"[Publisher] Skipping {episode_id} (missing metadata)")
            continue

        title = meta.get("title")
        if not title:
            print(f"[Publisher] Skipping {episode_id} (missing title)")
            continue

        script = load_episode_script(episode_id)

        published_at = int(meta.get("timestamp", audio_path.stat().st_mtime))

        video_url = f"https://toknnews.com/video/{episode_id}.mp4"
        page_url  = f"https://toknnews.com/episodes/{episode_id}/"

        # -------------------------------------------------
        # Write episode page (idempotent)
        # -------------------------------------------------
        ep_dir = PUBLIC_EPISODES_DIR / episode_id
        ep_dir.mkdir(parents=True, exist_ok=True)

        html = PAGE_TEMPLATE.substitute(
            TITLE=title,
            DESCRIPTION="Autonomous AI-generated crypto and macro market broadcast.",
            VIDEO_URL=video_url,
            PAGE_URL=page_url
        )
        (ep_dir / "index.html").write_text(html)

        # -------------------------------------------------
        # Write script JSON (static, per episode)
        # -------------------------------------------------
        if script:
            script_path = PUBLIC_EPISODES_DIR / f"{episode_id}_script.json"
            script_path.write_text(json.dumps(script, indent=2))

        # -------------------------------------------------
        # Index entry
        # -------------------------------------------------
        index.append({
            "episode_id": episode_id,
            "title": title,
            "audio": f"/audio/{audio_path.name}",
            "video": f"/video/{episode_id}.mp4",
            "page":  f"/episodes/{episode_id}/",
            "published_at": published_at
        })

    # -----------------------------------------------------
    # Write index.json (sorted newest → oldest)
    # -----------------------------------------------------

    if not index:
        print("[Publisher] No publishable episodes — index not rewritten.")
        return

    index.sort(key=lambda x: x["published_at"], reverse=True)

    index_path = PUBLIC_EPISODES_DIR / "index.json"
    index_path.write_text(json.dumps(index, indent=2))

    print(f"[Publisher] Published {len(index)} episodes")

# -----------------------------------------------------
# ENTRYPOINT
# -----------------------------------------------------

if __name__ == "__main__":
    main()
