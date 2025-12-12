#!/usr/bin/env python3
"""
studio_episode.py
Backend routes for Episode Console (Preview → Approve → Render)
Compatible with EpisodeRunner v5.
"""

from flask import Blueprint, request, jsonify
import json
import os
import time

from backend.script_engine.episode_runner import (
    generate_episode_script,
    approve_and_render
)

EPISODE_DIR = "/opt/toknnews/data/episodes"
BLOCK_DIR   = "/opt/toknnews/data/blocks"

episode_bp = Blueprint("studio_episode", __name__, url_prefix="/api/studio/episode")


# ------------------------------------------------------------
# /preview — generate script only (NO AUDIO, NO RENDER)
# ------------------------------------------------------------
@episode_bp.route("/preview", methods=["POST"])
def preview_episode():
    data = request.json or {}
    mode = data.get("mode", "NEWS")
    cap  = int(data.get("cap", 10))
    skip = bool(data.get("skip_ingest", False))

    result = generate_episode_script(
        episode_id=None,
        skip_ingest=skip
    )

    if not result:
        return jsonify({"ok": False, "error": "Episode generation failed"}), 500

    return jsonify({
        "ok": True,
        "episode_id": result["episode_id"],
        "mode": result["mode"],
        "blocks": result["blocks"],
        "estimated_runtime_sec": result["audio_blocks"] and len(result["audio_blocks"]) or 0,
        "audio_blocks": result["audio_blocks"],
    })


# ------------------------------------------------------------
# /approve — commit edited script & launch rendering
# ------------------------------------------------------------
@episode_bp.route("/approve", methods=["POST"])
def approve_episode():
    data = request.json or {}
    episode_id = data.get("episode_id")
    edits      = data.get("edits", [])
    audio_blocks = data.get("audio_blocks", None)

    if not episode_id:
        return jsonify({"ok": False, "error": "Missing episode_id"}), 400

    # Load preview script
    preview_file = os.path.join(EPISODE_DIR, f"{episode_id}_preview.json")
    if not os.path.exists(preview_file):
        return jsonify({"ok": False, "error": "Preview not found"}), 404

    with open(preview_file, "r") as f:
        blocks = json.load(f)

    # Apply edits to blocks
    if edits:
        for i in range(min(len(edits), len(blocks))):
            blocks[i]["text"] = edits[i]

    # Save edited version
    edited_path = os.path.join(EPISODE_DIR, f"{episode_id}_edited.json")
    with open(edited_path, "w") as f:
        json.dump(blocks, f, indent=2)

    # Trigger audio + render pipeline
    render_result = approve_and_render(episode_id, audio_blocks)

    return jsonify({
        "ok": True,
        "episode_id": episode_id,
        "render": render_result
    })


# ------------------------------------------------------------
# /render — retry render without regenerating script
# ------------------------------------------------------------
@episode_bp.route("/render", methods=["POST"])
def render_retry():
    data = request.json or {}
    episode_id = data.get("episode_id")

    if not episode_id:
        return jsonify({"ok": False, "error": "Missing episode_id"}), 400

    edited_file = os.path.join(EPISODE_DIR, f"{episode_id}_edited.json")
    if not os.path.exists(edited_file):
        return jsonify({"ok": False, "error": "No edited script found"}), 404

    blocks = json.load(open(edited_file))

    # Reconstruct audio_blocks
    audio_blocks = [
        {
            "speaker": b["speaker"],
            "text": b["text"],
            "block_type": b["tag"]
        }
        for b in blocks
    ]

    render_result = approve_and_render(episode_id, audio_blocks)

    return jsonify({
        "ok": True,
        "episode_id": episode_id,
        "render": render_result
    })
