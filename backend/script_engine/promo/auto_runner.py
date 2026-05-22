#!/usr/bin/env python3
# ============================================================
# 🧩 TOKNNEWS — AUTO MODE ENGINE (OPENCLAW POSTING READY)
# ============================================================

from __future__ import annotations

import json
import os
import time

import requests

BASE_URL = "http://127.0.0.1:8800/api/studio"
FLAG_PATH = "/opt/toknnews/data/auto_mode.json"
INTERVAL = 300  # 5 minutes is safer for browser posting


def _safe_load_flag() -> dict:
    if not os.path.exists(FLAG_PATH):
        return {
            "enabled": False,
            "auto_post": False,
            "platform": "x",
        }
    try:
        return json.load(open(FLAG_PATH))
    except Exception:
        return {
            "enabled": False,
            "auto_post": False,
            "platform": "x",
        }


def is_enabled() -> bool:
    return bool(_safe_load_flag().get("enabled", False))


def auto_post_enabled() -> bool:
    return bool(_safe_load_flag().get("auto_post", False))


def auto_post_platform() -> str:
    return str(_safe_load_flag().get("platform", "x")).strip().lower()


def run_cycle():
    print("\n=== AUTO: GENERATE ===")

    try:
        r = requests.post(
            f"{BASE_URL}/promo/generate",
            json={
                "anchor": "chip",
                "promo_type": "signal",
                "top_news": True,
            },
            timeout=30,
        )
        print("RAW GENERATE:", r.text)
        data = r.json()

        if not data.get("ok"):
            print("AUTO ERROR: generate failed", data)
            return

        promo_id = data.get("promo_id")
        text = data.get("text")
        script = data.get("script")
        anchor = data.get("anchor")

        print("SELECTED:", data.get("source"))

        print("AUTO: rendering...")
        r2 = requests.post(
            f"{BASE_URL}/promo/approve",
            json={
                "text": text,
                "anchor": anchor,
                "promo_id": promo_id,
            },
            timeout=60,
        )
        print("RAW RENDER:", r2.text)

        print("AUTO: generating social...")
        r3 = requests.post(
            f"{BASE_URL}/promo/social",
            json={
                "script": script,
                "anchor": anchor,
                "promo_id": promo_id,
            },
            timeout=30,
        )
        print("RAW SOCIAL:", r3.text)

        if auto_post_enabled():
            platform = auto_post_platform()

            if not promo_id:
                print("AUTO ERROR: missing promo_id, skipping post")
            else:
                print(f"AUTO: posting via OpenClaw → {platform}")

                try:
                    r4 = requests.post(
                        f"{BASE_URL}/promo/post",
                        json={
                            "promo_id": promo_id,
                            "platform": platform,
                            "dry_run": False,
                        },
                        timeout=45,
                    )

                    print("RAW POST:", r4.text)

                    try:
                        post_data = r4.json()
                    except Exception:
                        print("AUTO ERROR: invalid JSON from post response")
                        post_data = None

                    if not post_data or not post_data.get("ok"):
                        print("AUTO ERROR: post failed", post_data)
                    else:
                        print("AUTO: post success ✔")

                except Exception as e:
                    print("AUTO ERROR: post exception", e)

        print("=== AUTO: COMPLETE ===")

    except Exception as e:
        print("AUTO ERROR:", e)


def run_loop():
    print("AUTO MODE STARTED")

    while True:
        if not is_enabled():
            print("AUTO MODE STOPPED")
            break

        run_cycle()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    run_loop()
