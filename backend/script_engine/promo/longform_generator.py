#!/usr/bin/env python3
# ============================================================
# 🧩 TOKNNEWS — LONG FORM WRITER (OPENCLAW INTEGRATED)
# ============================================================

from __future__ import annotations
from typing import Dict, Any

from backend.script_engine.promo.signal_snapshot import build_snapshot
from backend.script_engine.promo.local_llm_client import call_local_llm
from backend.script_engine.promo.openclaw_client import call_openclaw


# ============================================================
# 🔴 PROMPT (LOCAL FALLBACK)
# ============================================================

def build_longform_prompt(anchor: str, narratives: list) -> str:

    return f"""
You are {anchor}, a professional financial journalist for Token News.

DATA:
{narratives}

TASK:
Write a structured article.

RULES:
- Use ONLY provided data
- No outside knowledge
- No hype or filler
- No unrelated markets

STYLE:
- Financial news tone
- No blog-style openings
- No "In conclusion"
- Start directly with the event
- Each paragraph adds new information

STRUCTURE:
- Headline
- Opening paragraph
- 2–3 supporting paragraphs
- Closing summary

OUTPUT JSON:

{{
  "title": "...",
  "article": "..."
}}

No text outside JSON.
"""


# ============================================================
# 🔴 MAIN GENERATOR
# ============================================================

def generate_longform(payload: Dict[str, Any]) -> Dict[str, Any]:

    anchor = (payload.get("anchor") or "chip").strip().lower()
    use_openclaw = bool(payload.get("use_openclaw", False))

    snapshot = build_snapshot()
    narratives = snapshot.get("narratives", [])

    if not narratives:
        return {
            "ok": False,
            "error": "No narrative data available"
        }

    # ============================================================
    # 🔴 OPENCLAW PATH (PRIMARY IF ENABLED)
    # ============================================================

    if use_openclaw:
        try:
            result = call_openclaw(
                "longform_writer",
                {
                    "anchor": anchor,
                    "narratives": narratives
                }
            )

            if result and isinstance(result, dict) and result.get("article"):
                return {
                    "ok": True,
                    "title": result.get("title", "Market Update"),
                    "article": result["article"].strip(),
                    "anchor": anchor,
                    "source": "openclaw"
                }

        except Exception as e:
            print("OPENCLAW ERROR:", e)

    # ============================================================
    # 🔴 LOCAL LLM FALLBACK
    # ============================================================

    prompt = build_longform_prompt(anchor, narratives)

    raw = call_local_llm(prompt)

    print("\n================ LONGFORM RAW OUTPUT ================\n")
    print(raw)
    print("\n====================================================\n")

    import json
    import re

    # 🔴 normalize quotes
    cleaned = raw.replace("“", "\"").replace("”", "\"").replace("’", "'")

    start = cleaned.find("{")
    end = cleaned.rfind("}")

    if start != -1 and end != -1:
        json_str = cleaned[start:end + 1]

        # 🔴 fix newline issue inside JSON strings
        json_str = re.sub(
            r'("article":\s*")([\s\S]*?)(")',
            lambda m: m.group(1) + m.group(2).replace('\n', '\\n') + m.group(3),
            json_str
        )

        try:
            obj = json.loads(json_str)

            title = (obj.get("title") or "Market Update").strip()
            article = (obj.get("article") or "").strip()

            if article:
                return {
                    "ok": True,
                    "title": title,
                    "article": article,
                    "anchor": anchor,
                    "source": "local"
                }

        except Exception as e:
            print("JSON PARSE ERROR:", e)

    # ============================================================
    # 🔴 FINAL FALLBACK (NEVER FAIL)
    # ============================================================

    return {
        "ok": True,
        "title": "Market Update",
        "article": raw.strip(),
        "anchor": anchor,
        "source": "fallback"
    }
