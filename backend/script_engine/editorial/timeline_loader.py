#!/usr/bin/env python3
"""
timeline_loader.py

Purpose:
- Load latest ep_<id>_preview.json
- Convert timeline blocks into audio blocks for TTS
- ZERO business logic
- ZERO ID generation
- Episode ID derived from preview filename
"""

import json
from pathlib import Path

EPISODE_DIR = Path("/opt/toknnews/data/episodes")


def _resolve_latest_preview():
    previews = sorted(
        EPISODE_DIR.glob("ep_*_preview.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not previews:
        raise RuntimeError("No preview episodes found — cannot resolve episode_id")

    latest_preview = previews[0]
    episode_id = latest_preview.stem.replace("ep_", "").replace("_preview", "")

    return episode_id, latest_preview


def load_episode_audio_blocks():
    """
    Returns:
        episode_id (str)
        audio_blocks (list[dict])
    """

    episode_id, preview_path = _resolve_latest_preview()

    timeline = json.loads(preview_path.read_text())

    audio_blocks = []
    order = 0

    for block in timeline:
        btype = block.get("type")

        if btype in ("monologue", "transition", "interrupt", "aside"):
            speaker = block.get("speaker")
            text = block.get("text")

            if speaker and text:
                audio_blocks.append({
                    "episode_id": episode_id,
                    "speaker": speaker,
                    "text": text,
                    "block_type": btype,
                    "order": order,
                })
                order += 1

        elif btype == "dialogue":
            for turn in block.get("turns", []):
                speaker = turn.get("speaker")
                text = turn.get("text")

                if speaker and text:
                    audio_blocks.append({
                        "episode_id": episode_id,
                        "speaker": speaker,
                        "text": text,
                        "block_type": "dialogue",
                        "order": order,
                    })
                    order += 1

    if not audio_blocks:
        raise RuntimeError("No audio blocks extracted from preview timeline")

    return episode_id, audio_blocks
