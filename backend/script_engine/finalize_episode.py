#!/usr/bin/env python3
"""
finalize_episode.py

PURPOSE:
- Finalize ONE episode after render
- Episode identity is resolved from the latest PREVIEW (NOT audio)
- Generate title ONCE (GPT)
- Write ep_<id>_meta.json
- Idempotent: safe to re-run
- NEVER publish
"""

import json
import os
import time
from pathlib import Path
from dotenv import load_dotenv
import openai

# -----------------------------------------------------
# ENV
# -----------------------------------------------------

load_dotenv("/opt/toknnews/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

# -----------------------------------------------------
# PATHS
# -----------------------------------------------------

EPISODE_DIR = Path("/opt/toknnews/data/episodes")
AUDIO_DIR   = Path("/var/www/toknnews/data/audio")
VIDEO_DIR   = Path("/var/www/toknnews/data/video")

EPISODE_DIR.mkdir(parents=True, exist_ok=True)

# -----------------------------------------------------
# HELPERS
# -----------------------------------------------------

def resolve_latest_preview_episode() -> str:
    """
    Canonical identity resolution.
    Preview creates identity.
    """
    previews = sorted(
        EPISODE_DIR.glob("ep_*_preview.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    if not previews:
        raise RuntimeError("No preview episodes found")

    return previews[0].stem.replace("ep_", "").replace("_preview", "")


def load_preview(episode_id: str) -> list:
    path = EPISODE_DIR / f"ep_{episode_id}_preview.json"
    if not path.exists():
        raise RuntimeError(f"Missing preview: {path}")
    return json.loads(path.read_text())


def generate_title(preview: list) -> str:
    signals = []
    for block in preview:
        if block.get("type") == "dialogue":
            domain = block.get("domain", "markets")
            anchors = ", ".join(block.get("anchors", []))
            signals.append(f"{domain} ({anchors})")

    prompt = f"""
You are generating a TITLE for a ToknNews episode.

Signals covered:
{', '.join(signals)}

Rules:
- 6–12 words
- No punctuation at the end
- No emojis
- No hype
- Professional, sharp
- Market-aware
- Not generic

Return ONLY the title.
""".strip()

    rsp = openai.ChatCompletion.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=40,
        timeout=15,
    )

    return rsp.choices[0].message.content.strip()


def calculate_runtime(preview: list) -> int:
    return sum(int(b.get("runtime_sec", 30)) for b in preview)

# -----------------------------------------------------
# MAIN
# -----------------------------------------------------

def main():
    episode_id = resolve_latest_preview_episode()
    meta_path = EPISODE_DIR / f"ep_{episode_id}_meta.json"

    # -----------------------------
    # IDEMPOTENCY GUARARD
    # -----------------------------
    if meta_path.exists():
        print(f"[Finalize] Episode {episode_id} already finalized. Skipping.")
        return

    audio_path = AUDIO_DIR / f"ep_{episode_id}_final.mp3"
    video_path = VIDEO_DIR / f"ep_{episode_id}.mp4"

    if not audio_path.exists():
        raise RuntimeError(f"Missing audio: {audio_path}")

    if not video_path.exists():
        raise RuntimeError(f"Missing video: {video_path}")

    preview = load_preview(episode_id)

    runtime_sec = calculate_runtime(preview)
    title = generate_title(preview)

    meta = {
        "episode_id": episode_id,
        "title": title,
        "finalized_at": time.time(),
        "mode": "NEWS",
        "runtime_sec": runtime_sec,
        "audio": str(audio_path),
        "video": str(video_path),
        "preview_file": f"ep_{episode_id}_preview.json",
    }

    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"[Finalize] Episode finalized → {meta_path}")
    print(f"[Finalize] Title locked → {title}")

if __name__ == "__main__":
    main()
