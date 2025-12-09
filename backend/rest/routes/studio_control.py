#!/usr/bin/env python3
"""
studio_control.py — ToknNews Studio Control API v5
===================================================

Purpose:
- Allow Studio UI to generate scripts on demand
- Provide script preview JSON
- Allow user to APPROVE episodes ("Degen Approved")
- Trigger audio + UE render when approved
- Manual breaking-news episodes
- Toggle autonomous 24/7 mode
- Return episode history
"""

import os, json, time
from flask import Blueprint, request, jsonify

from backend.script_engine.episode_runner import (
    generate_episode_script,
    approve_and_render,
)
from backend.runtime.vault_loader import load_secrets


studio = Blueprint("studio", __name__)

SECRETS = load_secrets()
AUTO_MODE_FILE = "/opt/toknnews/data/autonomous_flag.json"


# -------------------------------------------------------
# UTILITIES
# -------------------------------------------------------

def _set_auto_mode(state: bool):
    with open(AUTO_MODE_FILE, "w") as f:
        json.dump({"autonomous": state}, f)

def _get_auto_mode() -> bool:
    if not os.path.exists(AUTO_MODE_FILE):
        return False
    try:
        return json.load(open(AUTO_MODE_FILE)).get("autonomous", False)
    except:
        return False


# -------------------------------------------------------
# 1) GENERATE A NEW EPISODE SCRIPT (MANUAL)
# -------------------------------------------------------

@studio.route("/episode/generate", methods=["POST"])
def api_generate_episode():
    """
    Called when user presses:
       “Generate Script”
    Produces:
       • episode_id
       • script blocks
       • preview JSON file
    """

    try:
        skip_ingest = request.json.get("skip_ingest", False)
        ep = generate_episode_script(skip_ingest=skip_ingest)

        if not ep:
            return jsonify({"ok": False, "error": "Generation failed"}), 500

        return jsonify({
            "ok": True,
            "episode_id": ep["episode_id"],
            "blocks": ep["blocks"],
            "preview_file": ep["preview_file"],
            "mode": ep["mode"]
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# -------------------------------------------------------
# 2) FETCH SCRIPT PREVIEW BY EPISODE ID
# -------------------------------------------------------

@studio.route("/episode/preview/<episode_id>", methods=["GET"])
def api_fetch_preview(episode_id):
    path = f"/opt/toknnews/data/episodes/{episode_id}_preview.json"
    if not os.path.exists(path):
        return jsonify({"ok": False, "error": "Preview not found"}), 404
    return jsonify({"ok": True, "preview": json.load(open(path))})


# -------------------------------------------------------
# 3) APPROVAL → TTS + UE RENDER
# -------------------------------------------------------

@studio.route("/episode/approve", methods=["POST"])
def api_approve():
    """
    User pressed:
       “Degen Approved”
    """

    try:
        payload = request.json
        episode_id   = payload["episode_id"]
        audio_blocks = payload["audio_blocks"]

        result = approve_and_render(episode_id, audio_blocks)

        return jsonify({
            "ok": True,
            "episode_id": episode_id,
            "audio": result["audio"],
            "video": result["video"],
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# -------------------------------------------------------
# 4) BREAKING NEWS — Single-story forced episode
# -------------------------------------------------------

@studio.route("/episode/breaking", methods=["POST"])
def api_breaking_episode():
    """
    Force-generate a BREAKING MODE episode immediately.
    Studio button will call this.
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


# -------------------------------------------------------
# 5) TOGGLE AUTONOMOUS MODE
# -------------------------------------------------------

@studio.route("/autonomous/set", methods=["POST"])
def api_set_auto():
    state = request.json.get("enabled", False)
    _set_auto_mode(bool(state))
    return jsonify({"ok": True, "autonomous": bool(state)})

@studio.route("/autonomous/status", methods=["GET"])
def api_get_auto():
    return jsonify({"ok": True, "autonomous": _get_auto_mode()})


# -------------------------------------------------------
# 6) EPISODE HISTORY
# -------------------------------------------------------

@studio.route("/episodes/history", methods=["GET"])
def api_history():
    """
    Studio wants to list published episodes
    """

    EP_DIR = "/opt/toknnews/data/episodes"
    results = []

    for f in os.listdir(EP_DIR):
        if f.endswith("_meta.json"):
            meta = json.load(open(os.path.join(EP_DIR, f)))
            results.append({
                "episode_id": meta["episode_id"],
                "timestamp": meta["timestamp"],
                "mode": meta["mode"],
                "runtime_sec": meta["estimated_runtime_sec"],
            })

    results = sorted(results, key=lambda x: x["timestamp"], reverse=True)
    return jsonify({"ok": True, "episodes": results})


# -------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------

@studio.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "time": time.time()})
