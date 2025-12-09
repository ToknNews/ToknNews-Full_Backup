#!/usr/bin/env python3
"""
TOKN Security Module — Password + TOTP + Setup State Machine
Production-Safe, Rotation-Ready, Audit-Logged
"""

import json
import time
from pathlib import Path
import pyotp
import bcrypt
from datetime import datetime, timezone

# -------------------------------------------------------------------
# Paths
# -------------------------------------------------------------------
BASE_DIR = Path("/opt/toknnews")
SECRETS_DIR = BASE_DIR / "data" / "secrets"
LOG_DIR = BASE_DIR / "logs"

PASSWORD_FILE = SECRETS_DIR / "studio_password.json"
TOTP_FILE = SECRETS_DIR / "studio_totp.json"
SETUP_FILE = SECRETS_DIR / "studio_setup_state.json"

AUDIT_LOG = LOG_DIR / "studio_access.log"

# -------------------------------------------------------------------
# Utilities
# -------------------------------------------------------------------

def utc_now():
    return datetime.now(timezone.utc).isoformat()


def audit(event: str, ip: str, detail: str = ""):
    """Write login/setup events to audit log."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    line = f"{utc_now()} {event} ip={ip} {detail}\n"
    with open(AUDIT_LOG, "a") as f:
        f.write(line)

# -------------------------------------------------------------------
# Rate Limiter
# -------------------------------------------------------------------

RATE_LIMIT_WINDOW = 60
RATE_LIMIT_MAX = 5
_attempts = {}

def rate_limited(ip: str) -> bool:
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW

    if ip not in _attempts:
        _attempts[ip] = []

    _attempts[ip] = [t for t in _attempts[ip] if t > window_start]

    if len(_attempts[ip]) >= RATE_LIMIT_MAX:
        return True

    _attempts[ip].append(now)
    return False

# -------------------------------------------------------------------
# Setup State Machine
# -------------------------------------------------------------------

VALID_STATES = [
    "SETUP_REQUIRED_PASSWORD",
    "SETUP_REQUIRED_TOTP",
    "SETUP_PENDING_VERIFY",
    "SETUP_COMPLETE",
]

def load_state():
    """Load setup state, defaulting to password setup."""
    if not SETUP_FILE.exists():
        save_state("SETUP_REQUIRED_PASSWORD")
        return "SETUP_REQUIRED_PASSWORD"

    try:
        data = json.loads(SETUP_FILE.read_text())
        return data.get("setup_state", "SETUP_REQUIRED_PASSWORD")
    except:
        return "SETUP_REQUIRED_PASSWORD"


def save_state(state: str):
    """Persist setup state to file."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)
    SETUP_FILE.write_text(json.dumps({
        "setup_state": state,
        "updated": utc_now()
    }, indent=2))


# -------------------------------------------------------------------
# Password Management
# -------------------------------------------------------------------

def load_password_hash():
    if not PASSWORD_FILE.exists():
        return None
    try:
        data = json.loads(PASSWORD_FILE.read_text())
        return data.get("password_hash")
    except:
        return None


def set_password_hash(new_password: str, ip: str):
    """Initial setup password creation."""
    hashed = bcrypt.hashpw(new_password.encode(), bcrypt.gensalt()).decode()

    PASSWORD_FILE.write_text(json.dumps({
        "password_hash": hashed,
        "updated": utc_now()
    }, indent=2))

    audit("SETUP_PASSWORD_CREATED", ip)
    save_state("SETUP_REQUIRED_TOTP")


# -------------------------------------------------------------------
# TOTP Management
# -------------------------------------------------------------------

def load_totp_secret():
    """Load or create TOTP secret."""
    SECRETS_DIR.mkdir(parents=True, exist_ok=True)

    if not TOTP_FILE.exists():
        secret = pyotp.random_base32()
        TOTP_FILE.write_text(json.dumps({
            "secret": secret,
            "created": utc_now(),
            "updated": utc_now(),
            "rotations": []
        }, indent=2))
        return secret

    data = json.loads(TOTP_FILE.read_text())
    return data["secret"]


def verify_totp_setup(token: str, ip: str):
    """Verify TOTP during setup step."""
    try:
        token = str(token).strip().zfill(6)
    except:
        audit("SETUP_TOTP_MALFORMED", ip)
        return False

    secret = load_totp_secret()
    totp = pyotp.TOTP(secret)

    if not totp.verify(token, valid_window=1):
        audit("SETUP_TOTP_INVALID", ip)
        return False

    audit("SETUP_TOTP_VERIFIED", ip)
    save_state("SETUP_COMPLETE")
    return True


# -------------------------------------------------------------------
# Login Verification Logic (unchanged except for setup awareness)
# -------------------------------------------------------------------

def verify_credentials(password: str, token: str, ip: str):
    """
    Unified Studio Login verification.
    Only allowed after setup is fully complete.
    """

    state = load_state()
    if state != "SETUP_COMPLETE":
        return {
            "ok": False,
            "error": {
                "code": "SETUP_NOT_COMPLETE",
                "message": "Studio setup must be completed first."
            }
        }

    # RATE LIMIT
    if rate_limited(ip):
        audit("LOGIN_FAIL_RATE_LIMIT", ip)
        return {
            "ok": False,
            "error": { "code": "RATE_LIMIT", "message": "Too many attempts. Try again shortly." }
        }

    # Missing fields
    if not password or not token:
        audit("LOGIN_FAIL_MISSING", ip)
        return {
            "ok": False,
            "error": { "code": "MISSING_CREDENTIALS", "message": "Password or code missing." }
        }

    # Password validation
    stored_hash = load_password_hash()
    if not stored_hash:
        audit("LOGIN_FAIL_PASSWORD_NOT_SET", ip)
        return {
            "ok": False,
            "error": { "code": "PASSWORD_NOT_SET", "message": "Password not configured." }
        }

    if not bcrypt.checkpw(password.encode(), stored_hash.encode()):
        audit("LOGIN_FAIL_BAD_PASSWORD", ip)
        return {
            "ok": False,
            "error": { "code": "INVALID_PASSWORD", "message": "Incorrect password." }
        }

    # TOTP validation
    try:
        token = str(token).strip().zfill(6)
    except:
        audit("LOGIN_FAIL_TOTP_MALFORMED", ip)
        return {
            "ok": False,
            "error": { "code": "MALFORMED_TOTP", "message": "Invalid token format." }
        }

    secret = load_totp_secret()
    totp = pyotp.TOTP(secret)

    if not totp.verify(token, valid_window=1):
        audit("LOGIN_FAIL_TOTP_INVALID", ip)
        return {
            "ok": False,
            "error": { "code": "INVALID_TOTP", "message": "Invalid authentication code." }
        }

    # Success
    audit("LOGIN_SUCCESS", ip)
    return {
        "ok": True,
        "session": "studio",
        "auth": "password+totp",
        "timestamp": int(time.time())
    }


# -------------------------------------------------------------------
# Setup State Public API Helpers
# -------------------------------------------------------------------

def get_setup_state():
    """Return structured state for frontend."""
    state = load_state()
    return {
        "ok": True,
        "state": state
    }
