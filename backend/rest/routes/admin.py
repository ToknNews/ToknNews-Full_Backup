#!/usr/bin/env python3
"""
admin.py — ToknNews Admin Routes (canonical, production-safe)

Responsibilities:
- Trigger canonical ingestion as a separate OS process
- Keep REST API responsive at all times
- Expose stable admin endpoints
- Provide safe placeholders for future systems

IMPORTANT:
- Ingestion MUST NOT run in-process
- No threading
- No async hacks
"""

import time
import subprocess
import sys
from flask import Blueprint, jsonify

admin_bp = Blueprint("admin_bp", __name__, url_prefix="/api/admin")


# ------------------------
# Ingestion trigger (CANONICAL, NON-BLOCKING)
# ------------------------
@admin_bp.route("/ingest", methods=["POST"])
def trigger_ingest():
    """
    Canonical ingestion trigger.

    UI → POST /api/admin/ingest
       → spawn separate ingestion process
       → immediate HTTP 202

    This prevents:
    - GIL starvation
    - Socket suspension
    - UI fetch failures
    """

    try:
        subprocess.Popen(
            [
                sys.executable,
                "-m",
                "backend.rest.routes.ingest_v2.run_cycle",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except Exception as e:
        return jsonify({
            "status": "error",
            "runner": "run_cycle",
            "error": str(e),
            "timestamp": time.time(),
        }), 500

    return jsonify({
        "status": "started",
        "runner": "run_cycle",
        "timestamp": time.time(),
    }), 202


# ------------------------
# Ingestion status (SAFE PLACEHOLDER)
# ------------------------
@admin_bp.route("/ingest", methods=["GET"])
def ingest_status():
    """
    Placeholder endpoint.

    Future versions may read from:
    - SQLite ingest_runs
    - ingest_history.jsonl
    """
    return jsonify({
        "status": "ok",
        "running": "unknown",
        "note": "Ingestion runs out-of-process; no live lock state tracked.",
    })


# ------------------------
# PD State (SAFE STUB)
# ------------------------
@admin_bp.route("/pd_state", methods=["GET"])
def pd_state():
    """
    Stub endpoint to preserve UI compatibility.
    """
    return jsonify({
        "status": "stub",
        "note": "PD state module temporarily disabled."
    })


# ------------------------
# StoryBank view (SAFE STUB)
# ------------------------
@admin_bp.route("/storybank", methods=["GET"])
def storybank_view():
    """
    Stub endpoint.

    StoryBank will later be backed by a real store.
    """
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
    """
    Stub endpoint for episode history analytics.
    """
    return jsonify({
        "episodes": [],
        "note": "Episodes history temporarily stubbed."
    })
