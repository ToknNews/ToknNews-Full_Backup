#!/usr/bin/env python3
# ============================================================
# 🧩 TOKNNEWS — PROMO RUNNER (SIMPLIFIED ENGINE)
# ============================================================
#
# ████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
# ╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
#    ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
#    ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
#    ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
#    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝
#
# Promo Runner (Simple Mode)
# ============================================================

from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict

from backend.script_engine.promo.promo_generator import generate_promo
from backend.script_engine.promo.promo_audio_renderer import render_promo_audio
from backend.script_engine.promo.promo_video_renderer import render_promo_video

EXPORT_DIR = Path("/opt/toknnews/output/promos")
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


# ============================================================
# HELPERS
# ============================================================

def _export_path(promo_id: str) -> Path:
    return EXPORT_DIR / f"{promo_id}.json"


# ============================================================
# 🔴 GENERATE PROMO (SIMPLE MODE)
# ============================================================

def generate_promo_artifact(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generates a single clean promo script (no variants)
    """

    promo = generate_promo(payload)

    # 🔴 Ensure required fields
    script = promo.get("script") or ""
    cta = promo.get("cta") or ""
    anchor = promo.get("anchor") or "chip"

    text = promo.get("text") or script

    # 🔴 normalize final text
    if cta:
        text = f"{script} {cta}".strip()

    promo_clean = {
        "promo_id": promo.get("promo_id"),
        "created_at": promo.get("created_at"),
        "anchor": anchor,
        "script": script,
        "cta": cta,
        "text": text,
        "length_sec": promo.get("length_sec"),
    }

    # 🔴 export
    out = _export_path(promo_clean["promo_id"])
    out.write_text(json.dumps(promo_clean, indent=2))

    promo_clean["export_json"] = str(out)

    return promo_clean


# ============================================================
# 🔴 RENDER PROMO (NO VARIANTS)
# ============================================================

def approve_and_render_promo(promo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Render a promo using a single script (no variants)
    """

    promo_id = promo.get("promo_id")
    anchor = (promo.get("anchor") or "chip").strip().lower()
    text = (promo.get("text") or "").strip()

    if not promo_id:
        raise RuntimeError("Promo missing promo_id")

    if not text:
        raise RuntimeError("Promo text missing")

    render_id = f"{promo_id}_main"

    # 🔴 AUDIO
    audio_path = render_promo_audio(
        anchor=anchor,
        text=text,
        render_id=render_id
    )

    # 🔴 VIDEO
    video_path = render_promo_video(render_id, audio_path)

    # 🔴 update export
    export_json = promo.get("export_json") or str(_export_path(promo_id))

    try:
        p = Path(export_json)
        base = json.loads(p.read_text()) if p.exists() else promo

        base["last_render"] = {
            "render_id": render_id,
            "audio": audio_path,
            "video": video_path,
            "ts": time.time(),
        }

        p.write_text(json.dumps(base, indent=2))
        export_json = str(p)

    except Exception:
        pass

    return {
        "promo_id": promo_id,
        "render_id": render_id,
        "audio": audio_path,
        "video": video_path,
        "export_json": export_json,
        "ok": True,
    }


# ============================================================
# 🔴 SOCIAL STUB (OPENCLAW READY)
# ============================================================

def generate_social_post(promo: Dict[str, Any]) -> Dict[str, Any]:
    """
    Placeholder for OpenClaw / social generation
    """

    headline = promo.get("script", "")

    return {
        "ok": True,
        "post": f"{headline}\n\nFollow @ToknNews for real-time updates."
    }
