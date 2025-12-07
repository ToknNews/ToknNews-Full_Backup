import time
import pyotp
from flask import Blueprint, request, jsonify, make_response

studio_auth_bp = Blueprint("studio_auth", __name__)

SECRET_FILE = "/opt/toknnews/data/studio_totp_secret"

FAILED_ATTEMPTS = {}
LOCKOUT_TIME = 60  # seconds
MAX_FAILS = 6

def load_secret():
    with open(SECRET_FILE, "r") as f:
        return f.read().strip()

def is_locked_out(ip):
    rec = FAILED_ATTEMPTS.get(ip)
    if not rec:
        return False
    if rec["fails"] >= MAX_FAILS and (time.time() - rec["last"]) < LOCKOUT_TIME:
        return True
    return False

def record_fail(ip):
    rec = FAILED_ATTEMPTS.setdefault(ip, {"fails": 0, "last": 0})
    rec["fails"] += 1
    rec["last"] = time.time()

@studio_auth_bp.post("/api/studio/login")
def login():
    ip = request.remote_addr

    if is_locked_out(ip):
        return jsonify({"ok": False, "error": "Too many attempts — wait 1 minute."})

    try:
        code = request.json["code"]
    except:
        return jsonify({"ok": False, "error": "Missing code"})

    totp = pyotp.TOTP(load_secret())

    if totp.verify(code, valid_window=1):
        FAILED_ATTEMPTS[ip] = {"fails": 0, "last": 0}
        resp = make_response(jsonify({"ok": True}))
        resp.set_cookie("tokn_session", "authenticated", httponly=True, samesite="Strict")
        return resp

    record_fail(ip)
    return jsonify({"ok": False, "error": "Invalid code"})
