#!/usr/bin/env python3
"""
studio_episode.py
Backend routes for Episode Console (Preview → Approve → Render)

This module is clean, isolated, and compatible with the
Episode Console in studio.js.
"""

from flask import Blueprint, request, jsonify
import json
import os
import time

from backend.script_engine.episode_runner import run_episode
from backend.render_controller import render_episode

EPISODE_DIR = "/opt/toknnews/data/episodes"
BLOCK_DIR   = "/opt/toknnews/data/blocks"

episode_bp = Blueprint("studio_episode", __name__,
                       url_prefix="/api/studio/episode")


# ------------------------------------------------------------
# /preview  → dry-run script generator (NO audio, NO render)
# ------------------------------------------------------------
@episode_bp.route("/preview", methods=["POST"])
def preview_episode():
    try:
        data = request.json or {}
        mode = data.get("mode", "NEWS")
        cap  = int(data.get("cap", 10))
        skip = bool(data.get("skip_ingest", False))

        result = run_episode(
            episode_id=None,
            skip_ingest=skip,
            daypart="evening",
            show_mode=mode
        )

        if not result:
            return jsonify({"ok": False, "error": "Episode generation failed."})

        # Trim to cap manually (run_episode already does this, but we enforce again)
        blocks = result["blocks"][:cap]

        return jsonify({
            "ok": True,
            "episode_id": result["episode_id"],
            "mode": result["mode"],
            "estimated_runtime_sec": result["estimated_runtime_sec"],
            "blocks": blocks
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------------------------------------
# /approve → apply user text edits & save final block file
# ------------------------------------------------------------
@episode_bp.route("/approve", methods=["POST"])
def approve_episode():
    try:
        data = request.json or {}
        episode_id = data.get("episode_id")
        edits = data.get("edits", [])

        if not episode_id:
            return jsonify({"ok": False, "error": "Missing episode_id"})

        block_file = f"{BLOCK_DIR}/{episode_id}_blocks.json"
        if not os.path.exists(block_file):
            return jsonify({"ok": False, "error": "Episode blocks not found."})

        with open(block_file, "r") as f:
            blocks = json.load(f)

        if len(blocks) != len(edits):
            return jsonify({"ok": False, "error": "Edit count mismatch."})

        # Apply text edits to each block
        for i, new_text in enumerate(edits):
            blocks[i]["text"] = new_text

        with open(block_file, "w") as f:
            json.dump(blocks, f, indent=2)

        return jsonify({"ok": True, "message": "Episode approved."})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ------------------------------------------------------------
# /render → kicks off full audio + Unreal metadata package
# ------------------------------------------------------------
@episode_bp.route("/render", methods=["POST"])
def render_ep():
    try:
        data = request.json or {}
        episode_id = data.get("episode_id")

        if not episode_id:
            return jsonify({"ok": False, "error": "Missing episode_id"})

        block_file = f"{BLOCK_DIR}/{episode_id}_blocks.json"
        if not os.path.exists(block_file):
            return jsonify({"ok": False, "error": "Episode blocks not found."})

        with open(block_file, "r") as f:
            blocks = json.load(f)

        # AUDIO will be handled by audio renderer
        final_path = render_episode(
            blocks=blocks,
            audio_file=None,          # Audio engine will compute internally
            episode_id=episode_id,
            mode="unreal"             # produce Unreal package
        )

        return jsonify({
            "ok": True,
            "message": "Render started.",
            "path": final_path
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500
