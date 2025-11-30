import os
import json
from datetime import datetime

LOG_DIR = "/var/www/toknnews-live/logs/director"
os.makedirs(LOG_DIR, exist_ok=True)

HUMAN_LOG = os.path.join(LOG_DIR, "director.log")
EVENT_STREAM = os.path.join(LOG_DIR, "director_events.jsonl")


def _timestamp() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def log_event(event_type: str, message: str, data: dict | None = None, tone: str = "day") -> None:
    """
    Writes a human-readable log entry + JSONL analytics event.

    tone: 'day', 'evening', 'late_night', 'overnight', 'breaking', 'weekend'
    """

    stamp = _timestamp()
    data = data or {}

    # --- Human log ---
    try:
        with open(HUMAN_LOG, "a") as f:
            f.write(f"[{stamp}] [{tone.upper()}] {event_type}: {message}\n")
    except Exception:
        # Never let logging break show generation
        pass

    # --- JSONL event stream ---
    event_payload = {
        "timestamp": stamp,
        "event_type": event_type,
        "message": message,
        "tone": tone,
        "data": data
    }
    try:
        with open(EVENT_STREAM, "a") as f:
            f.write(json.dumps(event_payload) + "\n")
    except Exception:
        # Also swallow errors here
        pass
