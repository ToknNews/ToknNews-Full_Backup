#!/usr/bin/env python3
"""
studio_episode.py
ToknNews Studio Episode API (CANONICAL)

Contracts:
- /preview  → generate script + timeline ONLY
- /approve  → render audio + video → finalize → publish
- /render   → re-render audio/video ONLY
"""

from flask import Blueprint, request, jsonify
import os
import threading
import traceback

from backend.script_engine.episode_runner import generate_episode_script

EPISODE_DIR = "/opt/toknnews/data/episodes"

episode_bp = Blueprint(
    "studio_episode",
    __name__,
    url_prefix="/api/studio/episode"
)

# ==========================================================
# GLOBAL ERROR HANDLER (CRITICAL STABILITY FIX)
# ==========================================================
@episode_bp.app_errorhandler(Exception)
def handle_unhandled_exception(e):
    """
    Catch ALL uncaught exceptions and ALWAYS return JSON.
    Prevents empty replies and HTML error pages.
    """
    traceback.print_exc()
    return jsonify({
        "ok": False,
        "error": str(e),
        "type": e.__class__.__name__,
    }), 500


# ==========================================================
# /preview — SCRIPT + TIMELINE ONLY
# ==========================================================
@episode_bp.route("/preview", methods=["POST"])
def preview_episode():
    payload = request.json or {}
    skip_ingest = bool(payload.get("skip_ingest", False))

    try:
        ep = generate_episode_script(skip_ingest=skip_ingest)

        return jsonify({
            "ok": True,
            "episode_id": ep["episode_id"],
            "title": ep["title"],
            "runtime_sec": ep["runtime_sec"],
            "blocks": ep["blocks"],
            "preview_file": ep["preview_file"],
        })

    except Exception as e:
        # Never re-raise — ALWAYS respond
        traceback.print_exc()
        return jsonify({
            "ok": False,
            "error": str(e),
            "stage": "preview_generation",
        }), 500


# ==========================================================
# /approve — AUDIO → VIDEO → FINALIZE → PUBLISH (ASYNC)
# ==========================================================
@episode_bp.route("/approve", methods=["POST"])
def approve_episode():
    data = request.json or {}
    episode_id = data.get("episode_id")

    if not episode_id:
        return jsonify({"ok": False, "error": "Missing episode_id"}), 400

    preview_path = f"{EPISODE_DIR}/ep_{episode_id}_preview.json"
    if not os.path.exists(preview_path):
        return jsonify({"ok": False, "error": "Preview not found"}), 404

    def _background_job(ep_id):
        try:
            from backend.script_engine.episode_runner import approve_and_render

            approve_and_render(ep_id)

            os.system(
                "python3 /opt/toknnews/backend/script_engine/finalize_episode.py"
            )
            os.system(
                "python3 /opt/toknnews/backend/script_engine/publish_static_episodes.py"
            )

            print(f"[STUDIO] Approved → finalized → published → {ep_id}")

        except Exception as e:
            print(f"[STUDIO ERROR] {ep_id}: {e}")
            traceback.print_exc()

    threading.Thread(
        target=_background_job,
        args=(episode_id,),
        daemon=True
    ).start()

    return jsonify({
        "ok": True,
        "episode_id": episode_id,
        "status": "approve_started"
    })


# ==========================================================
# /render — RE-RENDER AUDIO/VIDEO ONLY
# ==========================================================
@episode_bp.route("/render", methods=["POST"])
def render_retry():
    data = request.json or {}
    episode_id = data.get("episode_id")

    if not episode_id:
        return jsonify({"ok": False, "error": "Missing episode_id"}), 400

    meta_path = f"{EPISODE_DIR}/ep_{episode_id}_meta.json"
    if not os.path.exists(meta_path):
        return jsonify({"ok": False, "error": "Episode metadata not found"}), 404

    try:
        from backend.script_engine.episode_runner import approve_and_render
        result = approve_and_render(episode_id)

        return jsonify({
            "ok": True,
            "episode_id": episode_id,
            "audio": result.get("audio"),
            "video": result.get("video"),
        })

    except Exception as e:
        traceback.print_exc()
        return jsonify({"ok": False, "error": str(e)}), 500
