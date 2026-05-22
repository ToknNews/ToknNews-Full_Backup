#!/usr/bin/env python3
"""
# ============================================================
# 🧩 TOKNNEWS — ANALYTICS REST ENDPOINTS
# ============================================================
#
# ████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
# ╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
#    ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
#    ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
#    ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
#    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝
#
# SYSTEM: ToknNews REST API
# MODULE: analytics
# PURPOSE:
# - Serve analytics + ingestion outputs (clusters, sentiment, etc.)
# - Provide passthrough access to ToknClaw data (history endpoint)
# - Maintain strict 1:1 JSON contracts for frontend rendering
# ============================================================
"""

import json
from pathlib import Path
from flask import Blueprint, jsonify
import requests

ANALYTICS_DIR = Path("/opt/toknnews/data/analytics")

analytics_bp = Blueprint(
    "analytics_bp",
    __name__,
    url_prefix="/api/admin/analytics"
)

TOKNCLAW = "http://5.161.192.62:8787"


def _load_json_file(path):
    """Returns parsed JSON or sane fallback."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ============================================================
# 🔴 CORE ANALYTICS (LOCAL FILES)
# ============================================================

@analytics_bp.route("/sentiment", methods=["GET"])
def sentiment():
    data = _load_json_file(ANALYTICS_DIR / "sentiment.json")
    return jsonify(data or [])


@analytics_bp.route("/domains", methods=["GET"])
def domains():
    data = _load_json_file(ANALYTICS_DIR / "domains.json")
    return jsonify(data or [])


@analytics_bp.route("/onchain", methods=["GET"])
def onchain():
    data = _load_json_file(ANALYTICS_DIR / "onchain.json")
    return jsonify(data or {})


@analytics_bp.route("/clusters", methods=["GET"])
def clusters():
    """
    Return clusters.json EXACTLY as written by ingestion.
    No transformations, no wrapping, no renaming.
    Guaranteed 1:1 passthrough.
    """
    path = ANALYTICS_DIR / "clusters.json"
    data = _load_json_file(path)
    return jsonify(data or [])


@analytics_bp.route("/episodes", methods=["GET"])
def episodes():
    path = ANALYTICS_DIR / "episodes.json"
    data = _load_json_file(path)
    return jsonify(data or [])


@analytics_bp.route("/narrative_blocks", methods=["GET"])
def narrative_blocks():
    path = ANALYTICS_DIR / "narrative_blocks.json"
    data = _load_json_file(path)
    return jsonify(data or [])


# ============================================================
# 🔴 TOKNCLAW INTEGRATION (CRITICAL FIX)
# ============================================================

@analytics_bp.route("/history")
def history():
    import requests
    from flask import jsonify

    try:
        r = requests.get("http://5.161.192.62:8787/history", timeout=5)

        if r.status_code != 200:
            return jsonify({
                "error": "upstream_error",
                "status": r.status_code,
                "text": r.text[:200]
            }), 502

        return jsonify(r.json())  # 🔴 THIS IS THE FIX

    except Exception as e:
        return jsonify({"error": str(e)}), 500
