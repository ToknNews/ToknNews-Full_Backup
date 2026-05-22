#!/usr/bin/env python3
"""
# ============================================================
# 🧩 TOKNNEWS — OPENCLAW CLIENT
# ============================================================
#
# Hardened HTTP client for OpenClaw task execution.
# ============================================================
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

import requests

OPENCLAW_URL = os.getenv("OPENCLAW_URL", "http://127.0.0.1:18789").rstrip("/")
OPENCLAW_TIMEOUT_SEC = int(os.getenv("OPENCLAW_TIMEOUT_SEC", "45"))


def call_openclaw(task: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Calls the OpenClaw gateway.

    Assumed request shape:
      POST {OPENCLAW_URL}/run
      {
        "task": "<task_name>",
        "input": { ... }
      }

    If your actual gateway uses a different path or schema,
    update THIS FILE only.
    """
    url = f"{OPENCLAW_URL}/run"

    body = {
        "task": task,
        "input": payload,
    }

    try:
        response = requests.post(
            url,
            json=body,
            timeout=OPENCLAW_TIMEOUT_SEC,
        )

        print("OPENCLAW URL:", url)
        print("OPENCLAW TASK:", task)
        print("OPENCLAW STATUS:", response.status_code)
        print("OPENCLAW RAW:", response.text[:2000])

        response.raise_for_status()

        data = response.json()
        if isinstance(data, dict):
            return data

        return {"ok": True, "raw": data}

    except Exception as exc:
        print("OPENCLAW CLIENT ERROR:", exc)
        return None
