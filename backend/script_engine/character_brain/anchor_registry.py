#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS CHARACTER BRAIN
Anchor Registry

Purpose
-------
Canonical production registry for all ToknNews anchors.

This file is the source-of-truth for:
• anchor identity
• provider routing
• OpenClaw agent ids
• ElevenLabs voice ids
• domain authority
• on-air usage policy
• delivery traits for downstream writing and TTS

Design Notes
------------
• Tokn-owned canonical registry
• OpenClaw consumes this registry
• timeline / PD / writers should reference this module
• supports mixed model routing across OpenAI + Grok
• future-ready for ElevenLabs v3 conditioning

Author: TOKN Systems
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List


# ---------------------------------------------------------
# CANONICAL REGISTRY
# ---------------------------------------------------------

ANCHOR_REGISTRY: Dict[str, Dict[str, Any]] = {
    "chip": {
        "id": "chip",
        "display_name": "Chip",
        "role": "Flagship Anchor — Rational Narrator",
        "openclaw_agent_id": "chip",
        "writer_backend": "openai",
        "writer_model": "gpt-5",
        "voice_id": "teAyVVX8spybXkITa1A0",
        "voice_model_hint": "eleven_v3",
        "domains": ["general", "macro", "markets", "breaking", "news"],
        "domain_weight": {
            "general": 1.0,
            "macro": 0.95,
            "markets": 0.92,
            "breaking": 0.96,
            "news": 0.90,
        },
        "panel_role": "host",
        "can_lead": True,
        "can_counter": True,
        "can_close": True,
        "can_interrupt": False,
        "host_priority": 1.0,
        "energy": 0.58,
        "style_tags": ["calm", "analytical", "structured", "data_first"],
        "forbidden_tags": ["hype", "meme", "slang", "overclaim"],
        "tts_profile": {
            "stability": 0.52,
            "similarity_boost": 0.80,
            "style": 0.18,
            "use_speaker_boost": True,
        },
    },
    "bond": {
        "id": "bond",
        "display_name": "Bond",
        "role": "Markets & Macro Anchor",
        "openclaw_agent_id": "bond",
        "writer_backend": "openai",
        "writer_model": "gpt-5",
        "voice_id": "ckPPrwZqzA7Vp7ceNunQ",
        "voice_model_hint": "eleven_v3",
        "domains": ["macro", "markets", "economics", "rates", "liquidity"],
        "domain_weight": {
            "macro": 1.0,
            "markets": 0.88,
            "economics": 0.95,
            "rates": 0.98,
            "liquidity": 0.97,
        },
        "panel_role": "analyst",
        "can_lead": True,
        "can_counter": True,
        "can_close": False,
        "can_interrupt": False,
        "host_priority": 0.20,
        "energy": 0.54,
        "style_tags": ["macro", "skeptical", "disciplined", "old_school"],
        "forbidden_tags": ["hype", "retail_slang", "meta_jokes"],
        "tts_profile": {
            "stability": 0.56,
            "similarity_boost": 0.78,
            "style": 0.16,
            "use_speaker_boost": True,
        },
    },
    "reef": {
        "id": "reef",
        "display_name": "Reef",
        "role": "DeFi Specialist — Highest Energy Anchor",
        "openclaw_agent_id": "reef",
        "writer_backend": "grok",
        "writer_model": "grok-4",
        "voice_id": "7pLXpsTZ3rOalpNWmYqI",
        "voice_model_hint": "eleven_v3",
        "domains": ["defi", "onchain", "altcoins", "protocols", "yield"],
        "domain_weight": {
            "defi": 1.0,
            "onchain": 0.78,
            "altcoins": 0.92,
            "protocols": 0.96,
            "yield": 0.95,
        },
        "panel_role": "analyst",
        "can_lead": True,
        "can_counter": True,
        "can_close": False,
        "can_interrupt": False,
        "host_priority": 0.18,
        "energy": 0.79,
        "style_tags": ["fast", "sharp", "opportunistic", "protocol_native"],
        "forbidden_tags": ["legalese", "wooden_tone"],
        "tts_profile": {
            "stability": 0.42,
            "similarity_boost": 0.76,
            "style": 0.34,
            "use_speaker_boost": True,
        },
    },
    "lawson": {
        "id": "lawson",
        "display_name": "Lawson",
        "role": "Regulatory & Policy Anchor",
        "openclaw_agent_id": "lawson",
        "writer_backend": "openai",
        "writer_model": "gpt-5",
        "voice_id": "Wz0W8ilvy9oYu7DeKWfB",
        "voice_model_hint": "eleven_v3",
        "domains": ["regulation", "law", "policy", "compliance"],
        "domain_weight": {
            "regulation": 1.0,
            "law": 0.98,
            "policy": 0.96,
            "compliance": 0.94,
        },
        "panel_role": "analyst",
        "can_lead": True,
        "can_counter": True,
        "can_close": False,
        "can_interrupt": False,
        "host_priority": 0.18,
        "energy": 0.50,
        "style_tags": ["authoritative", "legal", "measured", "stern"],
        "forbidden_tags": ["meme", "hyperbole", "retail_slang"],
        "tts_profile": {
            "stability": 0.60,
            "similarity_boost": 0.80,
            "style": 0.12,
            "use_speaker_boost": True,
        },
    },
    "cash": {
        "id": "cash",
        "display_name": "Cash",
        "role": "Retail Trader Behavior",
        "openclaw_agent_id": "cash",
        "writer_backend": "grok",
        "writer_model": "grok-4",
        "voice_id": "b2zP5WtU6zW1RDLwR1VL",
        "voice_model_hint": "eleven_v3",
        "domains": ["markets", "retail", "sentiment", "culture", "positioning"],
        "domain_weight": {
            "markets": 0.94,
            "retail": 1.0,
            "sentiment": 0.90,
            "culture": 0.84,
            "positioning": 0.92,
        },
        "panel_role": "analyst",
        "can_lead": True,
        "can_counter": True,
        "can_close": False,
        "can_interrupt": False,
        "host_priority": 0.24,
        "energy": 0.74,
        "style_tags": ["witty", "fast", "behavioral", "trader_native"],
        "forbidden_tags": ["corporate", "lifeless", "legalese"],
        "tts_profile": {
            "stability": 0.44,
            "similarity_boost": 0.75,
            "style": 0.36,
            "use_speaker_boost": True,
        },
    },
    "ledger": {
        "id": "ledger",
        "display_name": "Ledger",
        "role": "On-chain Analyst",
        "openclaw_agent_id": "ledger",
        "writer_backend": "openai",
        "writer_model": "gpt-5",
        "voice_id": "NZN55afVwq1WHQJOwDCz",
        "voice_model_hint": "eleven_v3",
        "domains": ["onchain", "security", "infrastructure", "flows"],
        "domain_weight": {
            "onchain": 1.0,
            "security": 0.96,
            "infrastructure": 0.94,
            "flows": 0.97,
        },
        "panel_role": "analyst",
        "can_lead": True,
        "can_counter": True,
        "can_close": False,
        "can_interrupt": False,
        "host_priority": 0.16,
        "energy": 0.48,
        "style_tags": ["forensic", "compressed", "flow_based", "precise"],
        "forbidden_tags": ["fluff", "hype", "sloppy_claims"],
        "tts_profile": {
            "stability": 0.58,
            "similarity_boost": 0.81,
            "style": 0.10,
            "use_speaker_boost": True,
        },
    },
    "ivy": {
        "id": "ivy",
        "display_name": "Ivy",
        "role": "Behavioral Economics & Sentiment",
        "openclaw_agent_id": "ivy",
        "writer_backend": "openai",
        "writer_model": "gpt-5",
        "voice_id": "Iw2tTyxZnwTODhsmOq00",
        "voice_model_hint": "eleven_v3",
        "domains": ["sentiment", "psychology", "macro", "behavior"],
        "domain_weight": {
            "sentiment": 1.0,
            "psychology": 0.98,
            "macro": 0.68,
            "behavior": 0.96,
        },
        "panel_role": "analyst",
        "can_lead": False,
        "can_counter": True,
        "can_close": False,
        "can_interrupt": False,
        "host_priority": 0.12,
        "energy": 0.62,
        "style_tags": ["warm", "human", "behavioral", "reflective"],
        "forbidden_tags": ["meme", "overconfidence"],
        "tts_profile": {
            "stability": 0.50,
            "similarity_boost": 0.79,
            "style": 0.20,
            "use_speaker_boost": True,
        },
    },
    "penny": {
        "id": "penny",
        "display_name": "Penny",
        "role": "Retail / Human-Interest",
        "openclaw_agent_id": "penny",
        "writer_backend": "openai",
        "writer_model": "gpt-5",
        "voice_id": "7WqwVs6Wqe0yEev6QDxV",
        "voice_model_hint": "eleven_v3",
        "domains": ["retail", "mass-market", "lifestyle", "human_interest"],
        "domain_weight": {
            "retail": 0.90,
            "mass-market": 1.0,
            "lifestyle": 0.95,
            "human_interest": 0.98,
        },
        "panel_role": "translator",
        "can_lead": False,
        "can_counter": False,
        "can_close": False,
        "can_interrupt": False,
        "host_priority": 0.08,
        "energy": 0.57,
        "style_tags": ["accessible", "warm", "plain_english"],
        "forbidden_tags": ["jargon_wall", "edgelord"],
        "tts_profile": {
            "stability": 0.54,
            "similarity_boost": 0.77,
            "style": 0.18,
            "use_speaker_boost": True,
        },
    },
    "bitsy": {
        "id": "bitsy",
        "display_name": "Bitsy",
        "role": "Meta Interruption Goblin",
        "openclaw_agent_id": "bitsy",
        "writer_backend": "grok",
        "writer_model": "grok-4",
        "voice_id": "VOkhRocQyiAQg2RF9A5e",
        "voice_model_hint": "eleven_v3",
        "domains": ["meta", "social", "late-night", "culture"],
        "domain_weight": {
            "meta": 1.0,
            "social": 0.96,
            "late-night": 0.98,
            "culture": 0.90,
        },
        "panel_role": "interrupt",
        "can_lead": False,
        "can_counter": False,
        "can_close": False,
        "can_interrupt": True,
        "host_priority": 0.01,
        "energy": 0.92,
        "style_tags": ["meta", "chaotic", "short", "mischievous"],
        "forbidden_tags": ["analysis", "long_form", "serious"],
        "tts_profile": {
            "stability": 0.34,
            "similarity_boost": 0.73,
            "style": 0.48,
            "use_speaker_boost": True,
        },
    },
    "vega": {
        "id": "vega",
        "display_name": "Vega",
        "role": "In-Booth Voice & Show Identity",
        "openclaw_agent_id": "vega",
        "writer_backend": "grok",
        "writer_model": "grok-4",
        "voice_id": "Ax1HxHll9ku8pGyIt6kK",
        "voice_model_hint": "eleven_v3",
        "domains": ["identity", "voiceover", "color", "promo"],
        "domain_weight": {
            "identity": 1.0,
            "voiceover": 0.98,
            "color": 0.92,
            "promo": 0.95,
        },
        "panel_role": "booth_voice",
        "can_lead": False,
        "can_counter": False,
        "can_close": True,
        "can_interrupt": False,
        "host_priority": 0.02,
        "energy": 0.66,
        "style_tags": ["booth", "signature", "short", "controlled"],
        "forbidden_tags": ["analysis", "rambling", "deep_take"],
        "tts_profile": {
            "stability": 0.46,
            "similarity_boost": 0.84,
            "style": 0.30,
            "use_speaker_boost": True,
        },
    },
}


# ---------------------------------------------------------
# REGISTRY HELPERS
# ---------------------------------------------------------

def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def list_anchor_ids() -> List[str]:
    return sorted(ANCHOR_REGISTRY.keys())


def get_anchor(anchor_id: str) -> Dict[str, Any]:
    key = clean(anchor_id).lower()
    if key in ANCHOR_REGISTRY:
        return deepcopy(ANCHOR_REGISTRY[key])
    return deepcopy(ANCHOR_REGISTRY["chip"])


def get_openclaw_agent_id(anchor_id: str) -> str:
    row = get_anchor(anchor_id)
    return clean(row.get("openclaw_agent_id")) or clean(anchor_id).lower()


def get_writer_backend(anchor_id: str) -> str:
    row = get_anchor(anchor_id)
    return clean(row.get("writer_backend")).lower() or "openai"


def get_writer_model(anchor_id: str) -> str:
    row = get_anchor(anchor_id)
    return clean(row.get("writer_model"))


def get_voice_id(anchor_id: str) -> str:
    row = get_anchor(anchor_id)
    return clean(row.get("voice_id"))


def get_tts_profile(anchor_id: str) -> Dict[str, Any]:
    row = get_anchor(anchor_id)
    return safe_dict(row.get("tts_profile"))


def get_domains(anchor_id: str) -> List[str]:
    row = get_anchor(anchor_id)
    return [clean(x).lower() for x in safe_list(row.get("domains")) if clean(x)]


def get_panel_role(anchor_id: str) -> str:
    row = get_anchor(anchor_id)
    return clean(row.get("panel_role")).lower()


def anchor_can_lead(anchor_id: str) -> bool:
    return bool(get_anchor(anchor_id).get("can_lead"))


def anchor_can_counter(anchor_id: str) -> bool:
    return bool(get_anchor(anchor_id).get("can_counter"))


def anchor_can_interrupt(anchor_id: str) -> bool:
    return bool(get_anchor(anchor_id).get("can_interrupt"))


def score_anchor_for_domain(anchor_id: str, domain: str) -> float:
    row = get_anchor(anchor_id)
    d = clean(domain).lower()
    weights = safe_dict(row.get("domain_weight"))
    if d in weights:
        try:
            return float(weights[d])
        except Exception:
            return 0.0
    return 0.0


def find_best_anchors_for_domain(domain: str, limit: int = 5) -> List[Dict[str, Any]]:
    scored: List[Dict[str, Any]] = []
    for anchor_id in list_anchor_ids():
        row = get_anchor(anchor_id)
        score = score_anchor_for_domain(anchor_id, domain)
        if score <= 0:
            continue
        scored.append(
            {
                "anchor_id": anchor_id,
                "display_name": clean(row.get("display_name")),
                "score": round(score, 4),
                "panel_role": clean(row.get("panel_role")).lower(),
                "writer_backend": clean(row.get("writer_backend")).lower(),
                "openclaw_agent_id": clean(row.get("openclaw_agent_id")),
            }
        )
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:max(1, limit)]


def export_openclaw_agent_manifest() -> Dict[str, Any]:
    """
    Tokn-owned agent manifest for later sync into OpenClaw config.
    """
    out: Dict[str, Any] = {"agents": {}}

    for anchor_id in list_anchor_ids():
        row = get_anchor(anchor_id)
        out["agents"][anchor_id] = {
            "display_name": clean(row.get("display_name")),
            "openclaw_agent_id": clean(row.get("openclaw_agent_id")),
            "writer_backend": clean(row.get("writer_backend")),
            "writer_model": clean(row.get("writer_model")),
            "voice_id": clean(row.get("voice_id")),
            "panel_role": clean(row.get("panel_role")),
            "domains": get_domains(anchor_id),
            "tts_profile": get_tts_profile(anchor_id),
        }

    return out


if __name__ == "__main__":
    import json
    print(json.dumps(export_openclaw_agent_manifest(), indent=2))
