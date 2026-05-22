#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS PERSONA ENGINE
Anchor Router

Purpose
-------
Runtime routing layer for ToknNews anchors.

This module converts a dialogue block into:
• host anchor
• lead analyst
• support analyst
• counter anchor
• optional interrupt anchor
• provider routing for each selected anchor

Design Notes
------------
• registry-driven
• deterministic and production-safe
• Chip remains host by default
• Vega is booth/promo only unless explicitly allowed
• Bitsy only enters when culture/meta rules permit
• ready for OpenClaw, OpenAI, Grok, and future newsletter/social verticals

Author: TOKN Systems
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.script_engine.character_brain.anchor_registry import (
    anchor_can_counter,
    anchor_can_interrupt,
    find_best_anchors_for_domain,
    get_anchor,
    get_openclaw_agent_id,
    get_writer_backend,
    get_writer_model,
)


# ---------------------------------------------------------
# NORMALIZATION / HELPERS
# ---------------------------------------------------------

DOMAIN_MAP = {
    "macro": "macro",
    "regulation": "regulation",
    "market": "markets",
    "markets": "markets",
    "crypto_major": "markets",
    "crypto_alt": "markets",
    "defi": "defi",
    "flows": "onchain",
    "onchain": "onchain",
    "news": "news",
    "crypto_culture": "culture",
    "culture": "culture",
    "sentiment": "culture",
}


def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def unique_preserve(items: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()

    for item in items:
        key = clean(item).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(key)

    return out


def normalize_domain(domain: str) -> str:
    d = clean(domain).lower()
    return DOMAIN_MAP.get(d, d if d else "general")


def _block_pd_hints(block: Dict[str, Any]) -> Dict[str, Any]:
    return safe_dict(block.get("pd_hints"))


def _block_editorial_hints(block: Dict[str, Any]) -> Dict[str, Any]:
    return safe_dict(block.get("editorial_hints"))


def _block_context(block: Dict[str, Any]) -> Dict[str, Any]:
    return safe_dict(block.get("context"))


# ---------------------------------------------------------
# POLICY
# ---------------------------------------------------------

DEFAULT_POLICY: Dict[str, Any] = {
    "host_anchor": "chip",
    "allow_chip_as_analyst": True,
    "allow_vega_in_panels": False,
    "allow_bitsy_interrupts": True,
    "max_panel_size": 4,
    "prefer_counter_when_debate": True,
    "prefer_second_analyst_when_complex": True,
    "late_night_mode": False,
}


# ---------------------------------------------------------
# CORE ROUTING
# ---------------------------------------------------------

def _candidate_ids_for_block(block: Dict[str, Any]) -> List[str]:
    domain = normalize_domain(clean(block.get("domain")))
    ranked = find_best_anchors_for_domain(domain, limit=8)
    ids = [clean(x.get("anchor_id")).lower() for x in ranked if clean(x.get("anchor_id"))]

    supplied = [
        clean(x).lower()
        for x in safe_list(block.get("anchor_candidates"))
        if clean(x)
    ]

    preferred = supplied + ids

    # ban Vega from live analysis panels by default
    preferred = [x for x in preferred if x != "vega"]

    return unique_preserve(preferred)


def _pick_lead_analyst(block: Dict[str, Any], policy: Dict[str, Any]) -> str:
    candidates = _candidate_ids_for_block(block)
    host = clean(policy.get("host_anchor") or "chip").lower()

    for candidate in candidates:
        if candidate == host and not bool(policy.get("allow_chip_as_analyst")):
            continue
        row = get_anchor(candidate)
        if bool(row.get("can_lead")):
            return candidate

    return "chip"


def _pick_support_analyst(block: Dict[str, Any], lead: str, policy: Dict[str, Any]) -> Optional[str]:
    candidates = _candidate_ids_for_block(block)
    editorial = _block_editorial_hints(block)
    pd_hints = _block_pd_hints(block)

    need_support = bool(editorial.get("complexity") == "high") or bool(pd_hints.get("requires_numeric"))
    if not need_support and not bool(policy.get("prefer_second_analyst_when_complex")):
        return None

    for candidate in candidates:
        if candidate == lead:
            continue
        if candidate == "bitsy":
            continue
        row = get_anchor(candidate)
        if bool(row.get("can_lead")) or clean(row.get("panel_role")) in {"analyst", "translator"}:
            return candidate

    return None


def _pick_counter_anchor(block: Dict[str, Any], lead: str, support: Optional[str], policy: Dict[str, Any]) -> Optional[str]:
    pd_hints = _block_pd_hints(block)
    editorial = _block_editorial_hints(block)

    if not bool(policy.get("prefer_counter_when_debate")):
        return None

    debate = bool(pd_hints.get("debate_potential")) or bool(editorial.get("debate"))
    if not debate:
        return None

    candidates = _candidate_ids_for_block(block)

    for candidate in candidates:
        if candidate in {lead, support}:
            continue
        if anchor_can_counter(candidate):
            return candidate

    return None


def _pick_interrupt_anchor(block: Dict[str, Any], policy: Dict[str, Any]) -> Optional[str]:
    if not bool(policy.get("allow_bitsy_interrupts")):
        return None

    domain = normalize_domain(clean(block.get("domain")))
    editorial = _block_editorial_hints(block)
    pd_hints = _block_pd_hints(block)

    if domain == "culture":
        return "bitsy"

    if bool(policy.get("late_night_mode")) and bool(pd_hints.get("social_heat", 0) >= 0.6):
        return "bitsy"

    if bool(editorial.get("tone") == "playful"):
        return "bitsy"

    return None


def build_anchor_packet(anchor_id: str, seat: str) -> Dict[str, Any]:
    row = get_anchor(anchor_id)

    return {
        "anchor_id": clean(row.get("id")).lower(),
        "display_name": clean(row.get("display_name")),
        "seat": clean(seat).lower(),
        "panel_role": clean(row.get("panel_role")).lower(),
        "writer_backend": get_writer_backend(anchor_id),
        "writer_model": get_writer_model(anchor_id),
        "openclaw_agent_id": get_openclaw_agent_id(anchor_id),
        "voice_id": clean(row.get("voice_id")),
        "voice_model_hint": clean(row.get("voice_model_hint")),
        "style_tags": safe_list(row.get("style_tags")),
        "forbidden_tags": safe_list(row.get("forbidden_tags")),
        "tts_profile": safe_dict(row.get("tts_profile")),
    }


def route_anchor_panel(
    block: Dict[str, Any],
    *,
    policy: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    merged_policy = dict(DEFAULT_POLICY)
    if isinstance(policy, dict):
        merged_policy.update(policy)

    domain = normalize_domain(clean(block.get("domain")))
    lead = _pick_lead_analyst(block, merged_policy)
    support = _pick_support_analyst(block, lead, merged_policy)
    counter = _pick_counter_anchor(block, lead, support, merged_policy)
    interrupt = _pick_interrupt_anchor(block, merged_policy)
    host = clean(merged_policy.get("host_anchor") or "chip").lower()

    ordered_ids = unique_preserve(
        [
            host,
            lead,
            support or "",
            counter or "",
        ]
    )

    anchor_packets = [build_anchor_packet(anchor_id, "panel") for anchor_id in ordered_ids if anchor_id]

    return {
        "narrative_id": clean(block.get("narrative_id")),
        "domain": domain,
        "host_anchor": build_anchor_packet(host, "host"),
        "lead_analyst": build_anchor_packet(lead, "lead"),
        "support_analyst": build_anchor_packet(support, "support") if support else None,
        "counter_anchor": build_anchor_packet(counter, "counter") if counter else None,
        "interrupt_anchor": build_anchor_packet(interrupt, "interrupt") if interrupt else None,
        "panel": anchor_packets,
        "panel_anchor_ids": [clean(x.get("anchor_id")).lower() for x in anchor_packets],
        "writer_backends": unique_preserve(
            [clean(x.get("writer_backend")).lower() for x in anchor_packets if clean(x.get("writer_backend"))]
        ),
        "openclaw_agents": unique_preserve(
            [clean(x.get("openclaw_agent_id")) for x in anchor_packets if clean(x.get("openclaw_agent_id"))]
        ),
        "routing_reason": {
            "debate_potential": bool(_block_pd_hints(block).get("debate_potential")),
            "requires_numeric": bool(_block_pd_hints(block).get("requires_numeric")),
            "complexity": clean(_block_editorial_hints(block).get("complexity") or "medium").lower(),
            "tone": clean(_block_editorial_hints(block).get("tone") or "analytical").lower(),
        },
    }


def route_anchor_lineup(
    dialogue_blocks: List[Dict[str, Any]],
    *,
    policy: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for block in dialogue_blocks:
        if not isinstance(block, dict):
            continue
        out.append(route_anchor_panel(block, policy=policy))
    return out


if __name__ == "__main__":
    import json
    sample = {
        "narrative_id": "sample_1",
        "domain": "macro",
        "pd_hints": {
            "debate_potential": True,
            "requires_numeric": True,
        },
        "editorial_hints": {
            "complexity": "high",
            "tone": "analytical",
        },
        "anchor_candidates": ["bond", "chip", "cash"],
    }
    print(json.dumps(route_anchor_panel(sample), indent=2))
