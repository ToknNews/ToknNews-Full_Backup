#!/usr/bin/env python3
"""
# ============================================================
# 🦞 TOKNCLAW — API PROXY (TOKNNEWS EDGE)
# ============================================================
#
# ████████╗ ██████╗ ██╗  ██╗███╗   ██╗ ██████╗██╗      █████╗ ██╗    ██╗
# ╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║██╔════╝██║     ██╔══██╗██║    ██║
#    ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██║     ██║     ███████║██║ █╗ ██║
#    ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║     ██║     ██╔══██║██║███╗██║
#    ██║   ╚██████╔╝██║  ██╗██║ ╚████║╚██████╗███████╗██║  ██║╚███╔███╔╝
#    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝╚═╝  ╚═╝ ╚══╝╚══╝
#
# SYSTEM: ToknNews → ToknClaw Proxy
# PURPOSE:
# - Securely expose ToknClaw endpoints to frontend
# - Normalize API surface under /api/toknclaw/*
# - Handle upstream errors gracefully
# ============================================================
"""
from flask import Blueprint, jsonify
import requests

# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

TOKNCLAW_BASE = "http://5.161.192.62:8787"
TIMEOUT = 20

# -----------------------------------------------------------
# BLUEPRINT
# -----------------------------------------------------------

toknclaw_bp = Blueprint("toknclaw", __name__)

# -----------------------------------------------------------
# PROXY CORE
# -----------------------------------------------------------

def proxy(path: str):
    url = f"{TOKNCLAW_BASE}/{path}"

    try:
        print(f"[TOKNCLAW PROXY] → {url}")

        r = requests.get(url, timeout=TIMEOUT)

        print(f"[TOKNCLAW PROXY] status={r.status_code} time={r.elapsed.total_seconds()}s")

        r.raise_for_status()

        return jsonify(r.json())

    except requests.exceptions.Timeout:
        print("[TOKNCLAW PROXY ERROR] Timeout")
        return jsonify({"error": "toknclaw timeout"}), 504

    except requests.exceptions.ConnectionError:
        print("[TOKNCLAW PROXY ERROR] Connection failed")
        return jsonify({"error": "toknclaw connection failed"}), 502

    except Exception as e:
        print(f"[TOKNCLAW PROXY ERROR] {e}")
        return jsonify({"error": str(e)}), 500

# -----------------------------------------------------------
# ROUTES
# -----------------------------------------------------------

@toknclaw_bp.route("/api/toknclaw/full_state")
def full_state():
    return proxy("full_state")


@toknclaw_bp.route("/api/toknclaw/portfolio")
def portfolio():
    return proxy("portfolio")


@toknclaw_bp.route("/api/toknclaw/sizing")
def sizing():
    return proxy("sizing")


@toknclaw_bp.route("/api/toknclaw/leverage")
def leverage():
    return proxy("leverage")


@toknclaw_bp.route("/api/toknclaw/decisions")
def decisions():
    return proxy("decisions")


@toknclaw_bp.route("/api/toknclaw/history")
def history():
    return proxy("history")


@toknclaw_bp.route("/api/toknclaw/health")
def health():
    return jsonify({
        "status": "ok",
        "service": "toknclaw_proxy"
    })


