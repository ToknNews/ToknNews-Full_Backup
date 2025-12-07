#!/usr/bin/env python3
"""
TOKN Control Studio — Secure Login (Password + TOTP)
"""

import json
from pathlib import Path
from flask import Blueprint, request, jsonify
from datetime import datetime
import bcrypt
import pyotp
import qrcode
import base64
from io import BytesIO

studio_bp = Blueprint("studio", __name__, url_prefix="/api/studio")

SECRETS_DIR = Path("/opt/toknnews/data/secrets")
PASSWORD_FILE = SECRETS_DIR / "tokn_studio_password.json"
TOTP_FILE = SECRETS_DIR / "tokn_studio_totp.json"


def load_password_hash():
    if not PASSWORD_FILE.exists():
        return None

    try:
        data = json.loads(PASSWORD_FILE.read_text())
        return data.get("password_hash")
    except:
        return None


def load_totp_secret():
    if not TOTP_FILE.exists():
        # Generate new secret if missing
        secret = pyotp.random_base32()
        TOTP_FILE.write_text(json.dumps({"secret": secret}, indent=2))
        return secret

    data = json.loads(TOTP_FILE.read_text())
    return data["secret"]


@studio_bp.get("/qrcode")
def generate_qr():
    """Returns QR code for enrolling TOKN Studio TOTP."""
    secret = load_totp_secret()
    issuer = "TOKN Control Studio"
    label = "admin@tokn"
    uri = pyotp.totp.TOTP(secret).provisioning_uri(label, issuer_name=issuer)

    qr = qrcode.make(uri)
    buf = BytesIO()
    qr.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return jsonify({"qr": f"data:image/png;base64,{b64}"})


@studio_bp.post("/login")
def login():
    data = request.json or {}
    password = data.get("password")
    token = data.get("token")

    if not password or not token:
        return jsonify({"ok": False, "error": "Missing credentials"}), 400

    # --- Validate password ---
    stored_hash = load_password_hash()
    if not stored_hash:
        return jsonify({"ok": False, "error": "Password not set"}), 500

    if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
        return jsonify({"ok": False, "error": "Invalid password"}), 403

    # --- Validate TOTP ---
    secret = load_totp_secret()
    totp = pyotp.TOTP(secret)

    if not totp.verify(token, valid_window=1):
        return jsonify({"ok": False, "error": "Invalid verification code"}), 403

    # If both pass:
    return jsonify({"ok": True, "message": "Login successful"})
