#!/usr/bin/env python3
"""
# ============================================================
# 🧩 TOKNNEWS — STUDIO CONTROL API (OPENCLAW INTEGRATED)
# ============================================================
#
# ████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
# ╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
#    ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
#    ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
#    ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
#    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝
#
# Studio Control — Promo + Social + Longform Engine
# ============================================================
"""

import os
import json
import time
import uuid
import subprocess
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify

from backend.script_engine.episode_runner import generate_episode_script
from backend.script_engine.promo.promo_generator import generate_promo
from backend.script_engine.promo.promo_audio_renderer import render_promo_audio
from backend.script_engine.promo.openclaw_posting_agent import post_social_via_openclaw

control_bp = Blueprint("studio_control", __name__, url_prefix="/api/studio")

DATA_DIR = "/opt/toknnews/data"
PROMO_DIR = Path("/opt/toknnews/output/promos")
CLUSTER_PATH = "/opt/toknclaw/data/analytics/cluster_active.json"
AUTO_FLAG = "/opt/toknnews/data/auto_mode.json"

PROMO_DIR.mkdir(parents=True, exist_ok=True)


# ======================================================
# HELPERS
# ======================================================

def _export_path(promo_id: str) -> Path:
    return PROMO_DIR / f"{promo_id}.json"


def _safe_load_json(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _get_auto_config():
    if not os.path.exists(AUTO_FLAG):
        return {
            "enabled": False,
            "auto_post": False,
            "platform": "x",
        }
    return json.load(open(AUTO_FLAG))


def _set_auto_config(enabled: bool, auto_post=None, platform=None):
    cfg = _get_auto_config()

    cfg["enabled"] = enabled

    if auto_post is not None:
        cfg["auto_post"] = auto_post

    if platform is not None:
        cfg["platform"] = platform

    with open(AUTO_FLAG, "w") as f:
        json.dump(cfg, f)


# ======================================================
# PROMO GENERATION
# ======================================================

@control_bp.route("/promo/generate", methods=["POST"])
def api_generate_promo():
    payload = request.json or {}

    try:
        promo = generate_promo(payload)

        promo_id = promo.get("promo_id")
        export_path = _export_path(promo_id)

        export_data = {
            "promo_id": promo_id,
            "anchor": promo.get("anchor"),
            "script": promo.get("script"),
            "cta": promo.get("cta"),
            "text": promo.get("text"),
            "source": promo.get("source"),
            "created_at": time.time(),
        }

        export_path.write_text(json.dumps(export_data, indent=2))

        return jsonify({"ok": True, **promo})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# RENDER PROMO
# ======================================================

@control_bp.route("/promo/approve", methods=["POST"])
def api_approve_promo():
    payload = request.json or {}

    text = payload.get("text")
    anchor = payload.get("anchor", "chip")
    promo_id = payload.get("promo_id")

    if not text:
        return jsonify({"ok": False, "error": "Missing text"}), 400

    render_id = f"promo_{uuid.uuid4().hex[:10]}"

    try:
        audio_path = render_promo_audio(anchor, text, render_id)

        if promo_id:
            export_path = _export_path(promo_id)
            if export_path.exists():
                data = _safe_load_json(export_path) or {}

                data["last_render"] = {
                    "render_id": render_id,
                    "audio": audio_path,
                    "ts": time.time(),
                }

                export_path.write_text(json.dumps(data, indent=2))

        return jsonify({
            "ok": True,
            "render": {
                "render_id": render_id,
                "audio": audio_path,
            }
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# SOCIAL GENERATION
# ======================================================

@control_bp.route("/promo/social", methods=["POST"])
def api_generate_social():
    payload = request.json or {}

    script = (payload.get("script") or "").strip()
    anchor = (payload.get("anchor") or "chip").strip().lower()
    promo_id = payload.get("promo_id")

    if not script:
        return jsonify({"ok": False, "error": "Missing script"}), 400

    try:
        post = f"{script}\n\nFollow @ToknNews for real-time updates."

        if promo_id:
            export_path = _export_path(promo_id)
            if export_path.exists():
                data = _safe_load_json(export_path) or {}

                data["social_post"] = {
                    "text": post,
                    "anchor": anchor,
                    "ts": time.time(),
                }

                export_path.write_text(json.dumps(data, indent=2))

        return jsonify({"ok": True, "post": post})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# LONG FORM
# ======================================================

@control_bp.route("/promo/longform", methods=["POST"])
def api_generate_longform():
    payload = request.json or {}

    try:
        from backend.script_engine.promo.longform_generator import generate_longform

        result = generate_longform(payload)

        if not result.get("ok"):
            return jsonify(result), 400

        promo_id = payload.get("promo_id")

        if promo_id:
            export_path = _export_path(promo_id)
            if export_path.exists():
                data = _safe_load_json(export_path) or {}

                data["long_form"] = {
                    "title": result["title"],
                    "article": result["article"],
                    "source": result.get("source"),
                    "ts": time.time(),
                }

                export_path.write_text(json.dumps(data, indent=2))

        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# AUTO MODE CONTROL
# ======================================================

@control_bp.route("/auto/start", methods=["POST"])
def api_auto_start():
    payload = request.json or {}

    auto_post = bool(payload.get("auto_post", False))
    platform = str(payload.get("platform") or "x").strip().lower()

    _set_auto_config(True, auto_post=auto_post, platform=platform)

    subprocess.Popen(
        [sys.executable, "-m", "backend.script_engine.promo.auto_runner"],
        cwd="/opt/toknnews",
    )

    return jsonify({
        "ok": True,
        "auto": True,
        "auto_post": auto_post,
        "platform": platform,
    })


@control_bp.route("/auto/stop", methods=["POST"])
def api_auto_stop():
    _set_auto_config(False)
    return jsonify({"ok": True, "auto": False})


@control_bp.route("/auto/status", methods=["GET"])
def api_auto_status():
    cfg = _get_auto_config()
    return jsonify({
        "ok": True,
        "auto": bool(cfg.get("enabled", False)),
        "auto_post": bool(cfg.get("auto_post", False)),
        "platform": str(cfg.get("platform") or "x"),
    })


# ======================================================
# OPENCLAW POSTING
# ======================================================

@control_bp.route("/promo/post", methods=["POST"])
def api_post_promo_social():
    payload = request.json or {}

    promo_id = str(payload.get("promo_id") or "").strip()
    platform = str(payload.get("platform") or "x").strip().lower()
    dry_run = bool(payload.get("dry_run", False))

    if not promo_id:
        return jsonify({"ok": False, "error": "Missing promo_id"}), 400

    try:
        result = post_social_via_openclaw(
            promo_id=promo_id,
            platform=platform,
            dry_run=dry_run,
        )

        if not result.get("ok"):
            return jsonify(result), 400

        export_path = _export_path(promo_id)
        if export_path.exists():
            data = _safe_load_json(export_path) or {}

            data["post_result"] = {
                "platform": platform,
                "dry_run": dry_run,
                "ts": time.time(),
                "result": result.get("result"),
            }

            export_path.write_text(json.dumps(data, indent=2))

        return jsonify(result)

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ======================================================
# CLUSTERS
# ======================================================

@control_bp.route("/clusters/active", methods=["GET"])
def api_clusters_active():
    path = Path(CLUSTER_PATH)

    if not path.exists():
        return jsonify({"ok": False, "error": "missing clusters"}), 404

    try:
        data = json.load(open(path))
        return jsonify({"ok": True, "clusters": data.get("clusters", {})})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)})


# ======================================================
# HEALTH
# ======================================================

@control_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"ok": True, "time": time.time()})
