#!/usr/bin/env python3
"""
studio_control.py — ToknNews Studio Control API v5.2
---------------------------------------------------

Responsibilities:
- Generate episode previews (NO audio/video)
- Approve episodes → trigger audio stitching (+ future video)
- Control autonomous mode
- Control GPT clustering flags
- Serve episode history for Studio UI
"""

import os
import json
import time
from flask import Blueprint, request, jsonify

from backend.script_engine.episode_runner import (
    generate_episode_script,
    approve_and_render,
)
from backend.runtime.vault_loader import load_secrets


# ======================================================
# BLUEPRINT
# ======================================================

# IMPORTANT: Studio Console expects routes under /api/studio/*
control_bp = Blueprint(
    "studio_control",
    __name__,
    url_prefix="/api/studio"
)

SECRETS = load_secrets()

DATA_DIR = "/opt/toknnews/data"
EP_DIR   = f"{DATA_DIR}/episodes"
AUTO_MODE_FILE = f"{DATA_DIR}/autonomous_flag.json"
GPT_FLAG_FILE  = f"{DATA_DIR}/enable_gpt_clusters.json"


# ======================================================
# AUTONOMOUS MODE HELPERS
# ======================================================

def _set_auto_mode(state: bool):
    with open(AUTO_MODE_FILE, "w") as f:
        json.dump({"autonomous": bool(state)}, f)

def _get_auto_mode() -> bool:
    if not os.path.exists(AUTO_MODE_FILE):
        return False
    try:
        return json.load(open(AUTO_MODE_FILE)).get("autonomous", False)
    except Exception:
        return False


# ======================================================
# EPISODE: GENERATE PREVIEW (NO AUDIO / NO VIDEO)
# ======================================================

@control_bp.route("/episode/generate", methods=["POST"])
def api_generate_episode():
    """
    Generates a PREVIEW ONLY.
    No audio, no video.
    """
    try:
        payload = request.json or {}
        skip_ingest = payload.get("skip_ingest", False)

        ep = generate_episode_script(skip_ingest=skip_ingest)

        return jsonify({
            "ok": True,
            "episode_id": ep["episode_id"],
            "mode": ep["mode"],
            "blocks": ep["blocks"],
            "preview_file": ep["preview_file"],
            "runtime_sec": ep["runtime_sec"]
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# EPISODE: FETCH PREVIEW
# ======================================================

@control_bp.route("/episode/preview/<episode_id>", methods=["GET"])
def api_fetch_preview(episode_id):
    path = f"{EP_DIR}/{episode_id}_preview.json"
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": "Preview not found"}), 404

    return jsonify({
        "ok": True,
        "preview": json.load(open(path))
    })


# ======================================================
# EPISODE: APPROVAL → AUDIO + STITCH (+ VIDEO LATER)
# ======================================================

@control_bp.route("/episode/approve", methods=["POST"])
def api_approve_episode():
    """
    Triggers:
    - TTS block rendering
    - Audio stitching
    - (Optional) video render
    """
    try:
        payload = request.json or {}

        episode_id   = payload.get("episode_id")
        audio_blocks = payload.get("audio_blocks")

        if not episode_id or not audio_blocks:
            return jsonify({
                "ok": False,
                "error": "episode_id and audio_blocks are required"
            }), 400

        result = approve_and_render(
            episode_id=episode_id,
            audio_blocks=audio_blocks
        )

        return jsonify({
            "ok": True,
            "episode_id": episode_id,
            "audio": result.get("audio"),
            "video": result.get("video")
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# EPISODE: BREAKING (FORCE FRESH INGEST)
# ======================================================

@control_bp.route("/episode/breaking", methods=["POST"])
def api_breaking_episode():
    """
    Forces fresh ingest + preview generation.
    """
    try:
        ep = generate_episode_script(skip_ingest=False)

        return jsonify({
            "ok": True,
            "episode_id": ep["episode_id"],
            "mode": ep["mode"],
            "preview_file": ep["preview_file"]
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# AUTONOMOUS MODE
# ======================================================

@control_bp.route("/autonomous/set", methods=["POST"])
def api_set_autonomous():
    enabled = bool((request.json or {}).get("enabled", False))
    _set_auto_mode(enabled)
    return jsonify({"ok": True, "autonomous": enabled})

@control_bp.route("/autonomous/status", methods=["GET"])
def api_get_autonomous():
    return jsonify({"ok": True, "autonomous": _get_auto_mode()})


# ======================================================
# GPT CLUSTERING FLAG
# ======================================================

@control_bp.route("/clusters/gpt/set", methods=["POST"])
def api_set_gpt_clusters():
    enabled = bool((request.json or {}).get("enabled", False))
    with open(GPT_FLAG_FILE, "w") as f:
        json.dump({"enabled": enabled}, f)
    return jsonify({"ok": True, "enabled": enabled})

@control_bp.route("/clusters/gpt/status", methods=["GET"])
def api_get_gpt_clusters():
    if not os.path.exists(GPT_FLAG_FILE):
        return jsonify({"ok": True, "enabled": False})

    try:
        enabled = json.load(open(GPT_FLAG_FILE)).get("enabled", False)
        return jsonify({"ok": True, "enabled": enabled})
    except Exception:
        return jsonify({"ok": True, "enabled": False})


# ======================================================
# EPISODE HISTORY (REVERSE CHRONOLOGICAL)
# ======================================================

@control_bp.route("/episodes/history", methods=["GET"])
def api_episode_history():
    results = []

    if not os.path.exists(EP_DIR):
        return jsonify({"ok": True, "episodes": []})

    for f in os.listdir(EP_DIR):
        if not f.endswith("_meta.json"):
            continue

        meta = json.load(open(os.path.join(EP_DIR, f)))
        results.append({
            "episode_id": meta.get("episode_id"),
            "timestamp": meta.get("timestamp", 0),
            "mode": meta.get("mode"),
            "runtime_sec": meta.get("runtime_sec"),
            "audio": meta.get("audio_file"),
            "video": meta.get("video_file"),
            "status": meta.get("status")
        })

    results.sort(key=lambda x: x["timestamp"], reverse=True)
    return jsonify({"ok": True, "episodes": results})


# ======================================================
# HEALTH
# ======================================================

@control_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "time": time.time()})
