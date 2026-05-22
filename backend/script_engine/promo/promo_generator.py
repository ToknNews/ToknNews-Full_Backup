#!/usr/bin/env python3
"""
# ============================================================
# 🧩 TOKNNEWS — PROMO GENERATOR ENGINE
# ============================================================
#
# ████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
# ╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
#    ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
#    ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
#    ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
#    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝
#
# Promo Generator (Production Hardened)
# ============================================================
"""

from __future__ import annotations

import json
import time
import uuid
from typing import Any, Dict

from backend.script_engine.promo.local_llm_client import call_local_llm
from backend.script_engine.promo.promo_prompt import build_prompt
from backend.script_engine.promo.signal_snapshot import build_snapshot


# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def _extract_json(text: str) -> dict | None:
    if not text:
        return None

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1:
        return None

    json_str = text[start:end + 1]

    try:
        return json.loads(json_str)
    except Exception as e:
        print("JSON PARSE ERROR:", e)
        print("RAW JSON BLOCK:", json_str[:500])
        return None


def _normalize_payload(payload: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(payload)

    out["promo_category"] = str(out.get("promo_category") or "signal").strip()
    out["promo_type"] = str(out.get("promo_type") or "breaking_news").strip()
    out["length_sec"] = int(out.get("length_sec") or 30)
    out["top_news"] = bool(out.get("top_news", False))

    return out


def _select_narrative(
    narratives: list[dict[str, Any]],
    promo_type: str,
) -> dict[str, Any] | None:
    if not narratives:
        return None

    # breaking_news always uses the top-ranked narrative
    if promo_type == "breaking_news":
        return narratives[0]

    # everything else rotates predictably every 30 seconds
    rotation_index = int(time.time() / 30) % len(narratives)
    return narratives[rotation_index]


# --------------------------------------------------
# MAIN GENERATOR
# --------------------------------------------------

def generate_promo(payload: Dict[str, Any]) -> Dict[str, Any]:
    payload = _normalize_payload(payload)

    snapshot = build_snapshot()
    narratives = snapshot.get("narratives", [])
    promo_type = payload.get("promo_type", "breaking_news")

    selected = _select_narrative(narratives, promo_type)

    payload["facts_snapshot"] = {
        "narratives": [selected] if selected else []
    }

    anchor = (payload.get("anchor") or "chip").strip().lower()

    prompt = build_prompt(payload)
    raw = call_local_llm(prompt)

    print("\n=== RAW LLM OUTPUT ===\n", raw)

    obj = _extract_json(raw)
    if not obj:
        raise RuntimeError("Invalid JSON from LLM")

    script = str(obj.get("script") or "").strip()
    cta = str(obj.get("cta") or "").strip()

    if not script:
        script = "No significant market developments detected."

    final_text = script
    if cta:
        final_text += " " + cta

    return {
        "ok": True,
        "promo_id": payload.get("promo_id") or f"promo_{uuid.uuid4().hex[:10]}",
        "created_at": time.time(),
        "anchor": anchor,
        "text": final_text,
        "script": script,
        "cta": cta,
        "length_sec": payload.get("length_sec", 30),
        "source": selected.get("title") if selected else None,
    }
