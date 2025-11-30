#!/usr/bin/env python3
"""
ToknNews Metrics Logger
-----------------------
Append timestamped metric entries to a JSONL file.
Designed to be lightweight, fault-tolerant, and safe for concurrent writes.
"""

import json, os, traceback
from datetime import datetime

LOG_PATH = "/var/www/toknnews/devdata/metrics.jsonl"

def log_metric(name: str, value, extra: dict = None):
    """
    Record a metric as one JSON line:
        {"time": "...", "name": "...", "value": ..., "extra": {...}}
    """
    try:
        os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
        entry = {
            "time": datetime.utcnow().isoformat(),
            "name": name,
            "value": value,
            "extra": extra or {}
        }
        with open(LOG_PATH, "a") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception:
        # Never crash the caller; just print error
        print(f"[MetricsLogger] ⚠️ Failed to write metric '{name}':")
        traceback.print_exc()
