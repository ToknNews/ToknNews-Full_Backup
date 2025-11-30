#!/usr/bin/env python3
"""
TOKNNews Heartbeat Updater
Keeps a live record of compiler health and recent status.
"""

import os, json, time

DATA_DIR = "/var/www/toknnews-live/data"
HEARTBEAT_PATH = os.path.join(DATA_DIR, "heartbeat.json")

def update_heartbeat(headline: str, sentiment: str, runtime: float, status: str = "success", error: str = None):
    os.makedirs(DATA_DIR, exist_ok=True)

    # Read current heartbeat if it exists
    hb = {}
    if os.path.exists(HEARTBEAT_PATH):
        try:
            hb = json.load(open(HEARTBEAT_PATH))
        except Exception:
            hb = {}

    total = hb.get("total_compiles", 0) + 1
    heartbeat = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "status": status,
        "last_headline": headline,
        "sentiment": sentiment,
        "runtime_seconds": runtime,
        "total_compiles": total,
        "last_error": error or "",
        "system_uptime": os.popen("uptime -p").read().strip()
    }

    with open(HEARTBEAT_PATH, "w") as f:
        json.dump(heartbeat, f, indent=2)

    print(f"[Heartbeat] 🩺 Updated ({status}) → {headline}")
    return heartbeat
