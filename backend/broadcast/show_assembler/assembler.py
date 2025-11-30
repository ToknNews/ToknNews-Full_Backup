#!/usr/bin/env python3
"""
ToknNews Show Assembler v1
Takes generated broadcast blocks and builds a unified
show folder with metadata + assets.
"""

import os
import json
from datetime import datetime
from shutil import copy2

BASE = "/var/www/toknnews-live/data"
SHOW_ROOT = f"{BASE}/shows"
BROADCAST_ROOT = f"{BASE}/broadcast"

os.makedirs(SHOW_ROOT, exist_ok=True)


def assemble_show(block_files):
    """
    block_files = list of absolute paths to broadcast block JSON files.
    Returns path to final episode folder.
    """

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    show_dir = os.path.join(SHOW_ROOT, ts)
    os.makedirs(show_dir, exist_ok=True)

    episode_meta = {
        "generated_at": ts,
        "segment_count": len(block_files),
        "segments": []
    }

    for path in block_files:
        with open(path, "r") as f:
            block = json.load(f)

        # Copy block JSON into show folder
        block_filename = os.path.basename(path)
        dest_json = os.path.join(show_dir, block_filename)
        copy2(path, dest_json)

        # Copy mixed WAV if present
        mix_path = block.get("segment_mix")
        if mix_path and os.path.exists(mix_path):
            dest_mix = os.path.join(show_dir, os.path.basename(mix_path))
            copy2(mix_path, dest_mix)
        else:
            dest_mix = None

        episode_meta["segments"].append({
            "block_json": block_filename,
            "segment_mix": os.path.basename(dest_mix) if dest_mix else None,
            "type": block.get("script_sequence", [{}])[0].get("type", "unknown")
        })

    # Write episode metadata
    meta_path = os.path.join(show_dir, "episode.json")
    with open(meta_path, "w") as f:
        json.dump(episode_meta, f, indent=2)

    # === Build master episode-level mix ===
    from .episode_mixer import build_episode_mix
    master_mix = build_episode_mix(show_dir)
    episode_meta["episode_master_mix"] = os.path.basename(master_mix) if master_mix else None

    # rewrite metadata to include master mix
    with open(meta_path, "w") as f:
        json.dump(episode_meta, f, indent=2)

    return show_dir
