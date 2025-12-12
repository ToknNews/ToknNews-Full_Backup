#!/usr/bin/env python3
"""
admin_logs.py — ToknNews Admin Logs API (Hardened)
-------------------------------------------------
Provides bounded, readable logs for Studio UI.
"""

import os
from flask import Blueprint, request, jsonify

admin_logs_bp = Blueprint(
    "admin_logs",
    __name__,
    url_prefix="/api/admin"
)

LOG_DIR = "/root/.pm2/logs"

LOG_MAP = {
    "rest":   "tokn-rest-out.log",
    "ingest": "tokn-ingest-out.log",
    "render": "tokn-render-out.log",
    "audio":  "tokn-audio-out.log",
}


def _tail(path: str, lines: int = 200) -> str:
    if not os.path.exists(path):
        return f"[missing log] {path}"

    with open(path, "r", errors="ignore") as f:
        return "".join(f.readlines()[-lines:])


@admin_logs_bp.route("/logs", methods=["GET"])
def get_logs():
    """
    Query params:
      service = rest | ingest | render | audio | all
      lines   = number of lines (default 200, max 1000)
    """
    service = request.args.get("service", "all")
    lines   = min(int(request.args.get("lines", 200)), 1000)

    output = []

    if service == "all":
        for name, fname in LOG_MAP.items():
            path = os.path.join(LOG_DIR, fname)
            output.append(f"\n===== TOKN {name.upper()} =====\n")
            output.append(_tail(path, lines))
    else:
        fname = LOG_MAP.get(service)
        if not fname:
            return jsonify({"ok": False, "error": "Invalid service"}), 400

        path = os.path.join(LOG_DIR, fname)
        output.append(_tail(path, lines))

    return jsonify({
        "ok": True,
        "text": "".join(output)
    })
