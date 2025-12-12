#!/usr/bin/env python3
"""
GPT Diagnostics Endpoint
Lets us directly test GPT cluster generation,
model availability, routing, and JSON output.
"""

import json
import traceback
from flask import Blueprint, jsonify

from backend.script_engine.analytics_cluster_gpt import generate_clusters
from backend.rest.routes.ingest_v2.ingest_controller import sentiment_count, domain_count

diagnostics_bp = Blueprint("diagnostics_bp", __name__, url_prefix="/api/admin/diagnostics")


@diagnostics_bp.route("/gpt", methods=["GET"])
def diagnostics_gpt():

    # Load a few recent stories from rolling_stories.json
    try:
        with open("/opt/toknnews/data/rolling_stories.json") as f:
            stories = json.load(f)
    except:
        return jsonify({
            "error": "Failed to load rolling_stories.json",
            "raw_exception": traceback.format_exc()
        }), 500

    sample = stories[:5]

    # Call GPT directly
    try:
        result = generate_clusters(sample)
    except Exception as e:
        return jsonify({
            "error": "GPT call failed",
            "message": str(e),
            "trace": traceback.format_exc(),
        }), 500

    return jsonify({
        "diagnostics": "GPT cluster test executed",
        "stories_used": len(sample),
        "stories_preview": [s.get("headline") for s in sample],
        "gpt_result": result
    })
