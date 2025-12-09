#!/usr/bin/env python3
"""
TOKN Control Studio — Multi-User Authentication System
Supports:
- Independent operator accounts
- Per-user bcrypt password hash
- Per-user TOTP secret
- Max-user enforcement (default: 2)
- QR provisioning per user
- Audit logging
"""

import json
import time
import threading
from pathlib import Path
from datetime import datetime, timezone
import bcrypt
import pyotp

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
BASE_DIR = Path("/opt/toknnews/data/secrets")
USERS_FILE = BASE_DIR / "studio_users.json"
AUDIT_FILE = Path("/opt/toknnews/logs/studio_access.log")

# Thread-safe write lock
_file_lock = threading.Lock()

# Hard operator limit
MAX_USERS = 2


# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------
def utc_now():
    return datetime.now(timezone.utc).isoformat()


def audit(event: str, detail: str = ""):
    AUDIT_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = f"{utc_now()} {event} {detail}\n"
    with open(AUDIT_FILE, "a") as f:
        f.write(line)


def load_users():
    if not USERS_FILE.exists():
        # Initialize with only admin user placeholder (no password yet)
        data = {
            "max_users": MAX_USERS,
            "users": []
        }
        USERS_FILE.write_text(json.dumps(data, indent=2))
        return data

    try:
        return json.loads(USERS_FILE.read_text())
    except:
        return {"max_users": MAX_USERS, "users": []}


def save_users(data):
    with _file_lock:
        USERS_FILE.write_text(json.dumps(data, indent=2))


# -------------------------------------------------------------------
# User creation
# -------------------------------------------------------------------
def create_user(username: str, password: str):
    users = load_users()

    if len(users["users"]) >= users.get("max_users", MAX_USERS):
        return {
            "ok": False,
            "error": {
                "code": "USER_LIMIT_REACHED",
                "message": f"Studio limited to {users.get('max_users', MAX_USERS)} operators."
            }
        }

    # Prevent duplicates
    for u in users["users"]:
        if u["username"].lower() == username.lower():
            return {
                "ok": False,
                "error": {
                    "code": "USER_EXISTS",
                    "message": "Username already exists."
                }
            }

    secret = pyotp.random_base32()
    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    entry = {
        "username": username,
        "password_hash": pw_hash,
        "totp_secret": secret,
        "created": utc_now(),
        "active": True
    }

    users["users"].append(entry)
    save_users(users)

    audit("USER_CREATED", f"username={username}")

    return {
        "ok": True,
        "username": username,
        "totp_secret": secret
    }


# -------------------------------------------------------------------
# Disable user
# -------------------------------------------------------------------
def disable_user(username: str):
    users = load_users()
    for u in users["users"]:
        if u["username"].lower() == username.lower():
            u["active"] = False
            save_users(users)
            audit("USER_DISABLED", f"username={username}")
            return {"ok": True}

    return {"ok": False, "error": {"code": "NOT_FOUND", "message": "User not found"}}


# -------------------------------------------------------------------
# Get QR provisioning URI for user
# -------------------------------------------------------------------
def get_user_qr_uri(username: str):
    users = load_users()
    for u in users["users"]:
        if u["username"].lower() == username.lower() and u["active"]:
            secret = u["totp_secret"]
            issuer = "TOKN Control Studio"
            label = username
            uri = pyotp.totp.TOTP(secret).provisioning_uri(label, issuer_name=issuer)
            return {"ok": True, "uri": uri}

    return {"ok": False, "error": {"message": "User not active or missing"}}


# -------------------------------------------------------------------
# Login verification
# -------------------------------------------------------------------
def verify_user_credentials(username: str, password: str, token: str, ip=""):
    users = load_users()

    # Find user
    user = None
    for u in users["users"]:
        if u["username"].lower() == username.lower():
            user = u
            break

    if not user or not user.get("active", False):
        audit("LOGIN_FAIL_NO_USER", f"user={username} ip={ip}")
        return {
            "ok": False,
            "error": {"code": "INVALID_USER", "message": "Invalid user"}
        }

    # Password check
    if not bcrypt.checkpw(password.encode(), user["password_hash"].encode()):
        audit("LOGIN_FAIL_BAD_PASSWORD", f"user={username} ip={ip}")
        return {
            "ok": False,
            "error": {"code": "INVALID_PASSWORD", "message": "Incorrect password."}
        }

    # TOTP validation
    token = str(token).strip().zfill(6)
    totp = pyotp.TOTP(user["totp_secret"])

    if not totp.verify(token, valid_window=1):
        audit("LOGIN_FAIL_BAD_TOTP", f"user={username} ip={ip}")
        return {
            "ok": False,
            "error": {"code": "INVALID_TOTP", "message": "Incorrect verification code."}
        }

    audit("LOGIN_SUCCESS", f"user={username} ip={ip}")
    return {
        "ok": True,
        "user": username,
        "session": "studio",
        "auth": "password+totp",
        "timestamp": int(time.time())
    }
