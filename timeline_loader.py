#!/usr/bin/env python3
"""
timeline_loader.py

CLEAN ARCHITECTURE (v2)

Purpose:
- Resolve latest preview episode
- Load that preview directly
- Convert preview timeline into audio blocks for TTS
- ZERO static episode_timeline.json dependency
- Episode identity derived ONLY from preview filename
"""

import json
from pathlib import Path
from typing import Tuple, List, Dict

EPISODE_DIR = Path("/opt/toknnews/data/episodes")


# ============================================================
# Resolve Latest Preview (Single Source of Truth)
# ============================================================

def _resolve_latest_preview() -> Tuple[str, Path]:
    previews = sorted(
        EPISODE_DIR.glob("ep_*_preview.json"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )

    if not previews:
        raise RuntimeError("No preview episodes found")

    latest = previews[0]
    episode_id = latest.stem.replace("ep_", "").replace("_preview", "")

    return episode_id, latest


# ============================================================
# Audio Block Extraction
# ============================================================

def load_episode_audio_blocks() -> Tuple[str, List[Dict]]:

    episode_id, preview_path = _resolve_latest_preview()
    timeline = json.loads(preview_path.read_text())

    audio_blocks = []
    order = 0

    for block in timeline:
        btype = block.get("type")

        if btype in ("monologue", "transition", "interjection", "interrupt"):
            speaker = block.get("speaker")
            text = block.get("text")

            if not speaker or not text:
                continue

            audio_blocks.append({
                "episode_id": episode_id,
                "speaker": speaker.lower(),
                "text": text.strip(),
                "block_type": btype,
                "order": order,
            })
            order += 1

        elif btype == "dialogue":
            for turn in block.get("turns", []):
                speaker = turn.get("speaker")
                text = turn.get("text")

                if not speaker or not text:
                    continue

                audio_blocks.append({
                    "episode_id": episode_id,
                    "speaker": speaker.lower(),
                    "text": text.strip(),
                    "block_type": "dialogue",
                    "order": order,
                })
                order += 1

    if not audio_blocks:
        raise RuntimeError("No audio blocks extracted from preview timeline")

    return episode_id, audio_blocks
