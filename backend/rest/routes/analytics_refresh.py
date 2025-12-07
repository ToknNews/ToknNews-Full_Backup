#!/usr/bin/env python3
"""
Manual + programmatic refresh of LLM analytics.
"""

import json
from flask import Blueprint, jsonify

from backend.script_engine.analytics_llm import run_llm_analytics
from backend.script_engine.analytics_engine import load_gpt_clusters

REFRESH_PATH = "/opt/toknnews/data/analytics/llm_analytics.json"

refresh_bp = Blueprint("refresh_bp", __name__, url_prefix="/api/admin/analytics")

@refresh_bp.route("/refresh_llm", methods=["POST"])
def refresh_llm():
    clusters = load_gpt_clusters().get("clusters", [])
    prev = None

    result = run_llm_analytics(clusters, prev_clusters=prev)

    with open(REFRESH_PATH, "w") as f:
        f.write(json.dumps(result, indent=2))

    return jsonify(result)
