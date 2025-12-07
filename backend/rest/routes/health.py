#!/usr/bin/env python3
"""
health.py
ToknNews V2 — Health Check Endpoint
"""

from flask import Blueprint, jsonify
import time

health_bp = Blueprint("health_bp", __name__)

@health_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "service": "toknnews_rest",
        "timestamp": time.time()
    })
