#!/usr/bin/env python3
"""
analytics_status.py — Tracks GPT narrative engine health
"""

import json, time
from pathlib import Path

STATUS_PATH = Path("/opt/toknnews/data/analytics/engine_status.json")

def update_status(source):
    status = {
        "gpt_success": 0,
        "gpt_failure": 0,
        "last_gpt_success": None,
        "last_gpt_failure": None,
    }

    if STATUS_PATH.exists():
        try:
            status = json.loads(STATUS_PATH.read_text())
        except:
            pass

    now = time.time()

    if source == "gpt":
        status["gpt_success"] += 1
        status["last_gpt_success"] = now
    else:
        status["gpt_failure"] += 1
        status["last_gpt_failure"] = now

    STATUS_PATH.write_text(json.dumps(status, indent=2))
    return status
