#!/usr/bin/env python3
"""
TOKN Control Studio — Multi-User Login & User Management API
"""

import base64
import json
from io import BytesIO
from flask import Blueprint, request, jsonify
import qrcode

from backend.internal.security.users import (
    load_users,
    create_user,
    disable_user,
    verify_user_credentials,
    get_user_qr_uri,
)

studio_bp = Blueprint("studio", __name__, url_prefix="/api/studio")


# ============================================================
# LOGIN — MULTI-USER
# ============================================================

@studio_bp.post("/login")
def login():
    data = request.json or {}

    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    token    = data.get("token", "").strip()

    ip = request.headers.get("X-Forwarded-For", request.remote_addr)

    result = verify_user_credentials(username, password, token, ip)
    return jsonify(result)


# ============================================================
# ADMIN: CREATE OPERATOR
# ============================================================

@studio_bp.post("/users/create")
def create_operator():
    data = request.json or {}

    # BOOTSTRAP: If no users exist, allow creation without admin check
    users = load_users()
    if len(users.get("users", [])) == 0:
        username = data.get("username", "").strip()
        password = data.get("password", "").strip()
        if not username or not password:
            return jsonify({"ok": False, "error": {"message": "Username & password required for bootstrap"}}), 400

        result = create_user(username, password)
        return jsonify(result)

    # NORMAL MODE (after admin exists)
    admin_user = data.get("admin_username", "")
    admin_pw   = data.get("admin_password", "")
    admin_token = data.get("admin_token", "")

    # Verify admin identity
    check = verify_user_credentials(admin_user, admin_pw, admin_token)
    if not check.get("ok"):
        return jsonify({"ok": False, "error": {"message": "Admin authentication failed."}}), 403

    if admin_user != "admin":
        return jsonify({"ok": False, "error": {"message": "Only admin may create users."}}), 403

    # Create user normally
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    result = create_user(username, password)
    return jsonify(result)


# ============================================================
# ADMIN: DISABLE USER
# ============================================================

@studio_bp.post("/users/disable")
def disable_operator():
    data = request.json or {}

    admin_user = data.get("admin_username", "")
    admin_pw   = data.get("admin_password", "")
    admin_token = data.get("admin_token", "")

    # Verify admin first
    check = verify_user_credentials(admin_user, admin_pw, admin_token)
    if not check.get("ok"):
        return jsonify({"ok": False, "error": {"message": "Admin authentication failed."}}), 403

    if admin_user != "admin":
        return jsonify({"ok": False, "error": {"message": "Only admin may disable users."}}), 403

    target = data.get("username", "").strip()
    result = disable_user(target)
    return jsonify(result)


# ============================================================
# LIST USERS (ADMIN ONLY)
# ============================================================

@studio_bp.get("/users/list")
def list_users():
    auth_header = request.headers.get("X-Studio-Admin", "")

    if auth_header != "admin":
        return jsonify({"ok": False, "error": {"message": "Unauthorized"}}), 403

    data = load_users()
    # Never return password hashes
    out = []
    for u in data["users"]:
        out.append({
            "username": u["username"],
            "active": u.get("active", False),
            "created": u.get("created"),
        })
    return jsonify({"ok": True, "users": out})


# ============================================================
# QR CODE FOR SPECIFIC USER
# ============================================================

@studio_bp.get("/users/qrcode/<username>")
def user_qrcode(username):
    result = get_user_qr_uri(username)
    if not result.get("ok"):
        return jsonify(result), 404

    uri = result["uri"]

    qr = qrcode.make(uri)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return jsonify({"ok": True, "qr": f"data:image/png;base64,{b64}"})


