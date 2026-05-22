#!/usr/bin/env python3
# ============================================================
# 🧩 TOKNNEWS — POSTIZ CLIENT
# ============================================================

import os
import requests

POSTIZ_URL = os.getenv("POSTIZ_URL", "http://127.0.0.1:4007")
POSTIZ_API_KEY = os.getenv("POSTIZ_API_KEY")  # optional if enabled


def post_to_postiz(text: str, platform: str = "x"):
    try:
        headers = {
            "Content-Type": "application/json"
        }

        if POSTIZ_API_KEY:
            headers["Authorization"] = f"Bearer {POSTIZ_API_KEY}"

        payload = {
            "content": text,
            "platform": platform
        }

        r = requests.post(
            f"{POSTIZ_URL}/api/posts",
            json=payload,
            headers=headers,
            timeout=20
        )

        print("POSTIZ RAW:", r.text)

        return r.json()

    except Exception as e:
        print("POSTIZ ERROR:", e)
        return {"ok": False, "error": str(e)}
