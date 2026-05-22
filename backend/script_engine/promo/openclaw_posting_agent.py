#!/usr/bin/env python3
"""
# ============================================================
# 🧩 TOKNNEWS — POSTING AGENT (POSTIZ MODE)
# ============================================================
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from backend.script_engine.promo.postiz_client import post_to_postiz

PROMO_DIR = Path("/opt/toknnews/output/promos")


def _promo_path(promo_id: str) -> Path:
    return PROMO_DIR / f"{promo_id}.json"


def _safe_load_json(path: Path) -> Dict[str, Any] | None:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def post_social_via_openclaw(
    promo_id: str,
    platform: str = "x",
    dry_run: bool = False,
) -> Dict[str, Any]:

    path = _promo_path(promo_id)

    if not path.exists():
        return {"ok": False, "error": f"Promo not found: {promo_id}"}

    promo = _safe_load_json(path)
    if not promo:
        return {"ok": False, "error": "Failed to read promo JSON"}

    text = (promo.get("social_post") or {}).get("text", "").strip()

    if not text:
        return {"ok": False, "error": "No social_post.text found on promo"}

    if dry_run:
        return {
            "ok": True,
            "platform": platform,
            "promo_id": promo_id,
            "dry_run": True,
            "preview": text[:200]
        }

    # 🔴 POST VIA POSTIZ
    result = post_to_postiz(text, platform)

    return {
        "ok": bool(result),
        "platform": platform,
        "promo_id": promo_id,
        "result": result
    }
