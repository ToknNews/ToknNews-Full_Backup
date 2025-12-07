#!/usr/bin/env python3
"""
submit.py
ToknNews V2 — Flask Ingest v2 Submit Endpoint
(Replaces old FastAPI APIRouter version)
"""

from flask import Blueprint, request, jsonify
import subprocess
import json
import time
import os

ingest_v2_bp = Blueprint("ingest_v2_bp", __name__, url_prefix="/ingest/v2")

LIVE = "/var/www/toknnews-live/backend/live"

@ingest_v2_bp.route("/submit", methods=["POST"])
def submit_story():
    """Send enriched story payload to scene compiler (legacy pipeline)."""

    try:
        data = request.get_json(force=True)

        # Write temp json
        path = f"/var/www/toknnews-live/data/pending_story.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        # Trigger compiler
        subprocess.Popen(
            ["python3", f"{LIVE}/scene_compiler_live.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return jsonify({"status": "ok", "submitted_id": data.get("id")})

    except Exception as e:
        return jsonify({"status": "error", "detail": str(e)}), 500
