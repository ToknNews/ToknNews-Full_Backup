#!/usr/bin/env python3

"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS CHARACTER BRAIN
Persona Loader

Purpose
-------
Loads character personas from character_brain.json and exposes
stable runtime helpers for ToknNews.

This module supports:
• persona lookup
• voice lookup
• domain-to-anchor matching
• phrasing access
• cadence access
• rules access
• safe fallback behavior
• future ElevenLabs v3 conditioning support

Primary File
------------
/opt/toknnews/backend/script_engine/character_brain/character_brain.json

Author: TOKN Systems
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
BRAIN_PATH = BASE_DIR / "character_brain.json"


# ---------------------------------------------------------
# LOAD PERSONA BRAIN
# ---------------------------------------------------------

def _load_brain() -> Dict[str, Any]:
    try:
        payload = json.loads(BRAIN_PATH.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


_BRAIN = _load_brain()


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def _safe(character: str) -> Dict[str, Any]:
    key = clean(character).lower()
    return safe_dict(_BRAIN.get(key) or _BRAIN.get("chip") or {})


# ---------------------------------------------------------
# PUBLIC API
# ---------------------------------------------------------

def list_personas() -> List[str]:
    return sorted(_BRAIN.keys())


def load_persona(character: str) -> Dict[str, Any]:
    return _safe(character)


def get_display_name(character: str) -> str:
    p = _safe(character)
    return clean(p.get("display_name")) or clean(character).title() or "Chip"


def get_voice(character: str) -> str:
    p = _safe(character)
    return clean(p.get("voice_id"))


def get_role(character: str) -> str:
    p = _safe(character)
    return clean(p.get("role"))


def get_domains(character: str) -> List[str]:
    p = _safe(character)
    return [clean(x).lower() for x in safe_list(p.get("domains")) if clean(x)]


def get_persona_lines(character: str) -> List[str]:
    p = _safe(character)
    return [clean(x) for x in safe_list(p.get("persona")) if clean(x)]


def get_analysis_phrasing(character: str) -> List[str]:
    p = _safe(character)
    style = safe_dict(p.get("analysis_style"))
    return [clean(x) for x in safe_list(style.get("phrasing")) if clean(x)]


def get_analysis_structure(character: str) -> List[str]:
    p = _safe(character)
    style = safe_dict(p.get("analysis_style"))
    return [clean(x) for x in safe_list(style.get("structure")) if clean(x)]


def get_transition_phrasing(character: str, target_group: str = "anchor") -> List[str]:
    p = _safe(character)
    style = safe_dict(p.get("transition_style"))

    if target_group == "vega":
        return [clean(x) for x in safe_list(style.get("to_vega")) if clean(x)]

    if target_group == "reentry":
        return [clean(x) for x in safe_list(style.get("reentry")) if clean(x)]

    return [clean(x) for x in safe_list(style.get("to_anchor")) if clean(x)]


def get_risk_phrasing(character: str) -> List[str]:
    p = _safe(character)
    risk = safe_dict(p.get("risk_behavior"))
    return [clean(x) for x in safe_list(risk.get("phrasing")) if clean(x)]


def get_bias_profile(character: str) -> Dict[str, Any]:
    return safe_dict(_safe(character).get("bias"))


def get_lexicon(character: str) -> Dict[str, Any]:
    return safe_dict(_safe(character).get("lexicon"))


def get_cadence(character: str) -> Dict[str, Any]:
    return safe_dict(_safe(character).get("cadence"))


def get_rules(character: str) -> Dict[str, Any]:
    return safe_dict(_safe(character).get("rules"))


def get_gpt_rules(character: str) -> Dict[str, Any]:
    return safe_dict(_safe(character).get("gpt_rules"))


def get_latenight_profile(character: str) -> Dict[str, Any]:
    return safe_dict(_safe(character).get("latenight"))


def domain_matches(character: str, domain: str) -> bool:
    d = clean(domain).lower()
    return d in get_domains(character)


def find_best_personas_for_domain(domain: str, limit: int = 3) -> List[str]:
    d = clean(domain).lower()
    scored: List[tuple[str, int]] = []

    for name in list_personas():
        score = 0
        domains = get_domains(name)

        if d in domains:
            score += 3

        if d == "markets" and any(x in domains for x in ["macro", "markets", "breaking"]):
            score += 2

        if d == "culture" and any(x in domains for x in ["meta", "social", "retail", "sentiment", "late-night"]):
            score += 2

        if d == "onchain" and any(x in domains for x in ["onchain", "infrastructure", "security"]):
            score += 2

        if d == "defi" and any(x in domains for x in ["defi", "altcoins", "onchain"]):
            score += 2

        if score > 0:
            scored.append((name, score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return [name for name, _ in scored[:max(1, limit)]]


def build_persona_prompt_context(character: str) -> Dict[str, Any]:
    return {
        "character": clean(character).lower(),
        "display_name": get_display_name(character),
        "role": get_role(character),
        "domains": get_domains(character),
        "persona_lines": get_persona_lines(character),
        "analysis_phrasing": get_analysis_phrasing(character),
        "analysis_structure": get_analysis_structure(character),
        "transition_phrasing": get_transition_phrasing(character),
        "risk_phrasing": get_risk_phrasing(character),
        "lexicon": get_lexicon(character),
        "cadence": get_cadence(character),
        "rules": get_rules(character),
        "gpt_rules": get_gpt_rules(character),
        "latenight": get_latenight_profile(character),
        "voice_id": get_voice(character),
    }


def debug_summary() -> None:
    print("=== ToknNews Persona Loader Summary ===")
    for key in list_personas():
        p = load_persona(key)
        print(
            f"- {key} :: "
            f"display={clean(p.get('display_name'))} :: "
            f"voice={clean(p.get('voice_id'))} :: "
            f"domains={len(get_domains(key))}"
        )


if __name__ == "__main__":
    debug_summary()
