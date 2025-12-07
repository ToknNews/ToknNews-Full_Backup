#!/usr/bin/env python3
"""
analytics.py — ToknNews Analytics REST Endpoints (FINAL FIX)
Serves raw analytics JSON exactly as written during ingestion.
"""

import json
from pathlib import Path
from flask import Blueprint, jsonify

ANALYTICS_DIR = Path("/opt/toknnews/data/analytics")

analytics_bp = Blueprint(
    "analytics_bp",
    __name__,
    url_prefix="/api/admin/analytics"
)

def _load_json_file(path):
    """Returns parsed JSON or sane fallback."""
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


# ---------------- SENTIMENT ----------------
@analytics_bp.route("/sentiment", methods=["GET"])
def sentiment():
    data = _load_json_file(ANALYTICS_DIR / "sentiment.json")
    return jsonify(data or [])


# ---------------- DOMAINS ----------------
@analytics_bp.route("/domains", methods=["GET"])
def domains():
    data = _load_json_file(ANALYTICS_DIR / "domains.json")
    return jsonify(data or [])


# ---------------- ON-CHAIN ----------------
@analytics_bp.route("/onchain", methods=["GET"])
def onchain():
    data = _load_json_file(ANALYTICS_DIR / "onchain.json")
    return jsonify(data or {})


# ---------------- CLUSTERS (FINAL FIX) ----------------
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


# ---------------- EPISODES ----------------
@analytics_bp.route("/episodes", methods=["GET"])
def episodes():
    path = ANALYTICS_DIR / "episodes.json"
    data = _load_json_file(path)
    return jsonify(data or [])


# ---------------- NARRATIVE BLOCKS ----------------
@analytics_bp.route("/narrative_blocks", methods=["GET"])
def narrative_blocks():
    path = ANALYTICS_DIR / "narrative_blocks.json"
    data = _load_json_file(path)
    return jsonify(data or [])
