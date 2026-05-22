#!/usr/bin/env python3
"""
admin.py — ToknNews Minimal Admin Routes (stabilized)
This version avoids importing any missing modules (_load_bank, pd_state, etc.)
and only exposes safe endpoints needed right now.
"""

import json
import time
from flask import Blueprint, jsonify, request

from backend.rest.routes.ingest_v2.ingest_controller import run_ingestion

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")


# ------------------------
# Ingestion trigger
# ------------------------
@admin_bp.route("/ingest", methods=["POST"])
def trigger_ingest():
    stories = run_ingestion()
    return jsonify({
        "status": "ok",
        "timestamp": time.time(),
        "total": len(stories),
        "rss_count": len([s for s in stories if s.get("source") == "RSS"]),
        "api_count": len([s for s in stories if s.get("source") == "API"])
    })


# ------------------------
# Ingestion status (placeholder)
# ------------------------
@admin_bp.route("/ingest", methods=["GET"])
def ingest_status():
    # You can later wire this into a real status store.
    return jsonify({
        "status": "ok",
        "note": "Ingestion status endpoint placeholder (no persistent state wired)."
    })


# ------------------------
# PD State (SAFE STUB)
# ------------------------
@admin_bp.route("/pd_state", methods=["GET"])
def pd_state():
    # Stub until we rewire a real pd_state module
    return jsonify({
        "status": "stub",
        "note": "PD state module temporarily disabled."
    })


# ------------------------
# StoryBank view (SAFE STUB)
# ------------------------
@admin_bp.route("/storybank", methods=["GET"])
def storybank_view():
    # Stub: no story bank wired here to avoid import errors.
    return jsonify({
        "count": 0,
        "stories": [],
        "note": "StoryBank view temporarily stubbed to keep API stable."
    })


# ------------------------
# Episodes history (SAFE STUB)
# ------------------------
@admin_bp.route("/analytics/episodes", methods=["GET"])
def episodes():
    # Stub episodes endpoint; can be wired to real data later.
    return jsonify({
        "episodes": [],
        "note": "Episodes history temporarily stubbed."
    })
