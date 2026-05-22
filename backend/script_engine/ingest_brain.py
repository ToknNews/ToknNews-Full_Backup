#!/usr/bin/env python3

"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS INGEST BRAIN (MEDIA VIEW ADAPTER)
ToknClaw → ToknNews Broadcast Bridge

Purpose
-------
Transforms ToknClaw media_view into:
• dialogue_blocks.json
• episode_context.json
• promo_payload.json

This module performs NO external ingestion.
It is a pure adapter between ToknClaw intelligence
and ToknNews broadcast preparation.

Primary Inputs
--------------
Preferred local sync target:
• /opt/toknnews/data/media_view.json

Optional fallback paths:
• /opt/toknclaw/data/views/media_view.json
• /opt/toknclaw/data/media_view.json

Primary Outputs
---------------
• /opt/toknnews/data/stories/dialogue_blocks.json
• /opt/toknnews/data/stories/episode_context.json
• /opt/toknnews/data/stories/promo_payload.json

Design Notes
------------
• no RSS / APIs / feed polling
• local-first media view loading
• atomic writes
• preserves ToknClaw story structure and metadata
• does NOT hardcode anchor assignment
• adds PD-ready hints without replacing ToknNews routing
• keeps promos rich and narrative-aware
• OpenClaw-ready metadata preserved where possible

Author: TOKN Systems
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple


# ---------------------------------------------------
# PATHS
# ---------------------------------------------------

MEDIA_VIEW_CANDIDATES = [
    Path(os.getenv("TOKN_MEDIA_VIEW_PATH", "")).expanduser() if os.getenv("TOKN_MEDIA_VIEW_PATH") else None,
    Path("/opt/toknnews/data/media_view.json"),
    Path("/opt/toknclaw/data/views/media_view.json"),
    Path("/opt/toknclaw/data/media_view.json"),
]

OUTPUT_DIALOGUE = Path("/opt/toknnews/data/stories/dialogue_blocks.json")
OUTPUT_CONTEXT = Path("/opt/toknnews/data/stories/episode_context.json")
OUTPUT_PROMO = Path("/opt/toknnews/data/stories/promo_payload.json")

TMP_DIALOGUE = OUTPUT_DIALOGUE.with_suffix(".tmp")
TMP_CONTEXT = OUTPUT_CONTEXT.with_suffix(".tmp")
TMP_PROMO = OUTPUT_PROMO.with_suffix(".tmp")


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def now_ts() -> float:
    return time.time()


def unique_preserve(items: List[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []

    for item in items:
        key = repr(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)

    return out


def write_json_atomic(path: Path, tmp_path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(payload, indent=2))
    tmp_path.replace(path)


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text())


def load_media_view() -> Tuple[Dict[str, Any], str]:
    checked: List[str] = []

    for candidate in MEDIA_VIEW_CANDIDATES:
        if candidate is None:
            continue

        checked.append(str(candidate))

        if not candidate.exists():
            continue

        try:
            data = _read_json(candidate)
        except Exception as e:
            raise RuntimeError(f"Failed reading media_view.json at {candidate}: {e}")

        if not isinstance(data, dict):
            raise RuntimeError(f"media_view.json at {candidate} is not a JSON object")

        return data, str(candidate)

    raise FileNotFoundError(
        "ToknClaw media_view.json missing. Checked:\n- "
        + "\n- ".join(checked)
    )


def normalize_domain(domain: str) -> str:
    d = clean(domain).lower()

    mapping = {
        "crypto_major": "markets",
        "crypto_alt": "markets",
        "crypto_culture": "culture",
        "market": "markets",
        "flows": "onchain",
        "news": "news",
        "macro": "macro",
        "regulation": "regulation",
        "defi": "defi",
    }

    return mapping.get(d, d if d else "general")


def build_anchor_candidates(raw_domain: str, entity_domain: str, supporting_signal_types: List[str]) -> List[str]:
    raw_d = clean(raw_domain).lower()
    entity_d = clean(entity_domain).lower()
    joined = " ".join(clean(x).lower() for x in supporting_signal_types)

    # Important:
    # We do NOT force anchors here.
    # We only provide ranked candidates for downstream routing.
    candidates: List[str] = []

    if raw_d == "macro":
        candidates.extend(["bond", "chip"])
    elif raw_d == "regulation":
        candidates.extend(["lawson", "bond", "chip"])
    elif raw_d == "defi":
        candidates.extend(["reef", "ledger", "chip"])
    elif raw_d == "flows":
        candidates.extend(["ledger", "cash", "chip"])
    elif raw_d == "market":
        candidates.extend(["cash", "chip", "bond"])
    elif raw_d == "crypto_major":
        candidates.extend(["chip", "cash", "ledger"])
    elif raw_d == "crypto_alt":
        candidates.extend(["chip", "reef", "cash"])
    elif raw_d == "crypto_culture":
        candidates.extend(["bitsy", "cash", "chip"])
    elif raw_d == "news":
        candidates.extend(["chip", "bond", "lawson"])

    if "protocol_" in joined:
        candidates.extend(["reef", "ledger"])
    if "large_token_transfer" in joined:
        candidates.extend(["ledger", "cash"])
    if "macro_indicator" in joined or "macro_news" in joined:
        candidates.extend(["bond", "chip"])
    if "news_theme" in joined:
        candidates.extend(["chip", "bond"])
    if "solana_memecoin" in joined or "pumpfun" in joined:
        candidates.extend(["bitsy", "cash", "chip"])

    if entity_d == "defi":
        candidates.extend(["reef", "ledger"])
    elif entity_d == "macro":
        candidates.extend(["bond", "chip"])
    elif entity_d == "crypto_culture":
        candidates.extend(["bitsy", "cash"])
    elif entity_d == "crypto_major":
        candidates.extend(["chip", "cash"])

    return unique_preserve([c for c in candidates if clean(c)])


def requires_numeric_probe(summary: str, signal_type: str, raw_domain: str) -> bool:
    text = f"{clean(summary)} {clean(signal_type)} {clean(raw_domain)}".lower()

    numeric_terms = [
        "$",
        "%",
        "price",
        "reading",
        "yield",
        "index",
        "volume",
        "open interest",
        "fees",
        "tvl",
        "transferred",
        "moved on",
        "score",
    ]

    return any(term in text for term in numeric_terms)


def has_debate_potential(signal_type: str, supporting_signal_types: List[str], raw_domain: str) -> bool:
    text = " ".join([clean(signal_type), clean(raw_domain)] + [clean(x) for x in supporting_signal_types]).lower()

    debate_terms = [
        "alpha",
        "strategy",
        "macro_news",
        "news_theme",
        "protocol_revenue",
        "protocol_tvl",
        "memecoin",
        "trending",
        "large_token_transfer",
    ]

    return any(term in text for term in debate_terms)


def build_thread_id(raw_domain: str, entity: str, signal_type: str) -> str:
    parts = [
        clean(raw_domain).lower() or "general",
        clean(entity).upper() or "NONE",
        clean(signal_type).lower() or "signal",
    ]
    return "::".join(parts)


def build_turns_from_card(
    title: str,
    summary: str,
    entity: str,
    raw_domain: str,
    signal_type: str,
    supporting_signal_types: List[str],
) -> List[Dict[str, Any]]:

    out: List[Dict[str, Any]] = []

    lead = clean(summary) or clean(title)
    if lead:
        out.append({"speaker": None, "text": lead})

    normalized_domain = normalize_domain(raw_domain)

    # --- DOMAIN-SPECIFIC FRAMING ---
    if normalized_domain == "macro":
        framing = "Macro conditions are shaping liquidity, risk appetite, and positioning across markets."
    elif normalized_domain == "regulation":
        framing = "Policy and legal shifts can reprice conviction faster than fundamentals."
    elif normalized_domain == "defi":
        framing = "Protocol-level activity reveals where capital is actually concentrating."
    elif normalized_domain == "onchain":
        framing = "On-chain flow often moves ahead of narrative recognition."
    elif normalized_domain == "markets":
        framing = "Price action must be validated by positioning and liquidity."
    elif normalized_domain == "culture":
        framing = "Retail sentiment and meme velocity can distort short-term price behavior."
    elif normalized_domain == "news":
        framing = "Headline flow can trigger repricing before consensus forms."
    else:
        framing = "This signal may influence the next narrative rotation."

    out.append({"speaker": None, "text": framing})

    # --- SUPPORTING CONTEXT ---
    support_text = ", ".join(supporting_signal_types[:5]) if supporting_signal_types else clean(signal_type)
    if entity:
        out.append({
            "speaker": None,
            "text": f"The focal entity is {entity}, supported by signals including {support_text}."
        })

    # --- TENSION / QUESTION (CRITICAL FOR DIALOGUE ENGINE) ---
    tension = ""
    if "alpha" in signal_type.lower():
        tension = "The question is whether this signal represents real positioning or short-term noise."
    elif "transfer" in signal_type.lower():
        tension = "The key question is whether this flow represents accumulation or redistribution."
    elif "macro" in signal_type.lower():
        tension = "The real question is whether macro conditions will reinforce or break this trend."
    elif "protocol" in signal_type.lower():
        tension = "The question is whether this activity translates into sustained value capture."
    elif "memecoin" in signal_type.lower():
        tension = "The risk is whether this momentum is sustainable or purely reflexive."

    if tension:
        out.append({"speaker": None, "text": tension})

    # --- FORWARD HOOK ---
    out.append({
        "speaker": None,
        "text": "What matters next is how this develops across the next phase of market activity."
    })

    return out[:6]

def select_cards_for_blocks(view: Dict[str, Any]) -> List[Tuple[str, Dict[str, Any]]]:
    segments = safe_dict(view.get("segments"))

    ordered_segments = [
        "macro",
        "news",
        "regulation",
        "crypto_major",
        "defi",
        "crypto_alt",
        "crypto_culture",
        "flows",
        "market",
    ]

    picked: List[Tuple[str, Dict[str, Any]]] = []

    for seg_name in ordered_segments:
        seg = safe_dict(segments.get(seg_name))
        cards = safe_list(seg.get("cards"))

        if not cards:
            continue

        # Keep richer coverage:
        # - macro/news get more slots
        # - culture/alt still represented
        # - empty segments ignored
        max_cards = 2
        if seg_name in {"macro", "news"}:
            max_cards = 3
        elif seg_name in {"crypto_culture"}:
            max_cards = 2

        seen_keys = set()

        for card in cards:
            card = safe_dict(card)

            entity = clean(card.get("entity"))
            title = clean(card.get("title"))
            summary = clean(card.get("summary"))
            key = f"{entity}::{title}::{summary}"

            if key in seen_keys:
                continue

            seen_keys.add(key)
            picked.append((seg_name, card))

            if len(seen_keys) >= max_cards:
                break

    picked.sort(
        key=lambda item: (
            safe_float(safe_dict(item[1]).get("story_score"), 0.0),
            safe_float(safe_dict(item[1]).get("confidence"), 0.0),
        ),
        reverse=True,
    )

    return picked[:18]


# ---------------------------------------------------
# DIALOGUE BLOCKS
# ---------------------------------------------------

def build_dialogue_blocks(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    selected = select_cards_for_blocks(view)
    blocks: List[Dict[str, Any]] = []

    for idx, (raw_domain, card) in enumerate(selected):
        card = safe_dict(card)

        entity = clean(card.get("entity"))
        title = clean(card.get("title"))
        summary = clean(card.get("summary"))
        signal_type = clean(card.get("signal_type"))
        entity_domain = clean(card.get("entity_domain"))
        confidence = safe_float(card.get("confidence"), 0.0)
        sentiment_score = safe_float(card.get("sentiment_score"), 0.0)
        story_score = safe_float(card.get("story_score"), 0.0)
        raw_url = card.get("raw_url")

        supporting_signal_types = unique_preserve([
            clean(x) for x in safe_list(card.get("supporting_signal_types")) if clean(x)
        ])

        if not title and not summary:
            continue

        thread_id = build_thread_id(raw_domain, entity, signal_type)

        block = {
            "narrative_id": f"{clean(raw_domain).lower()}_{idx}",
            "domain": normalize_domain(raw_domain),
            "raw_domain": clean(raw_domain),
            "anchors": [],
            "anchor_candidates": build_anchor_candidates(
                raw_domain=raw_domain,
                entity_domain=entity_domain,
                supporting_signal_types=supporting_signal_types,
            ),
            "heat": round(max(3.0, story_score), 2),
            "thesis": title or summary,
            "implication": summary or title,
            "dialogue": build_turns_from_card(
                title=title,
                summary=summary,
                entity=entity,
                raw_domain=raw_domain,
                signal_type=signal_type,
                supporting_signal_types=supporting_signal_types,
            ),
            "entities": [entity] if entity else [],
            "source": "toknclaw",
            "context": {
                "entity": entity,
                "signal_type": signal_type,
                "entity_domain": entity_domain,
                "supporting_signal_types": supporting_signal_types,
                "confidence": confidence,
                "sentiment_score": sentiment_score,
                "story_score": story_score,
                "raw_url": raw_url,
            },
            "pd_hints": {
                "is_filler": False,
                "domain": normalize_domain(raw_domain),
                "raw_domain": clean(raw_domain),
                "priority": round(story_score * (confidence + 0.5), 2),
                "segment_type": (
                    "lead" if story_score > 14
                    else "support" if story_score > 11
                    else "filler"
                ),

                "signal_type": signal_type,
                "thread_id": thread_id,
                "numeric_hook": summary or title,
                "requires_numeric": requires_numeric_probe(summary=summary, signal_type=signal_type, raw_domain=raw_domain),
                "debate_potential": has_debate_potential(
                    signal_type=signal_type,
                    supporting_signal_types=supporting_signal_types,
                    raw_domain=raw_domain,
                ),
                "volatility_risk": abs(sentiment_score),
                "social_heat": min(1.0, max(0.0, story_score / 20.0)),
            },
            "editorial_hints": {
                "debate": has_debate_potential(
                    signal_type=signal_type,
                    supporting_signal_types=supporting_signal_types,
                    raw_domain=raw_domain,
                ),
                "requires_numeric": requires_numeric_probe(
                    summary=summary,
                    signal_type=signal_type,
                    raw_domain=raw_domain,
                ),
                "tone": (
                    "analytical" if normalize_domain(raw_domain) in ["macro", "defi"]
                    else "reactive" if normalize_domain(raw_domain) in ["news", "culture"]
                    else "mixed"
                ),
                "complexity": (
                    "high" if story_score > 13
                    else "medium" if story_score > 10
                    else "low"
                ),
            },
            "showrunner_meta": {
                "block_thread_id": thread_id,
                "origin": "toknclaw_media_view",
                "confidence": confidence,
                "story_score": story_score,
                "entity_domain": entity_domain,
                "supporting_signal_types": supporting_signal_types,
                "raw_url": raw_url,

                # NEW
                "narrative_type": clean(signal_type),
                "drivers": supporting_signal_types[:5],
                "strength": "high" if story_score > 12 else "medium",
            },
            "showrunner_interventions": [
                intervention
                for intervention in [
                    {"type": "numeric_probe"} if requires_numeric_probe(summary=summary, signal_type=signal_type, raw_domain=raw_domain) else None,
                    {"type": "debate_escalation"} if has_debate_potential(signal_type=signal_type, supporting_signal_types=supporting_signal_types, raw_domain=raw_domain) else None,
                    {"type": "culture_injection"} if normalize_domain(raw_domain) == "culture" else None,
                ]
                if intervention is not None
            ],
        }

        blocks.append(block)

    blocks.sort(
        key=lambda x: (
            safe_float(x.get("heat"), 0.0),
            safe_float(safe_dict(x.get("context")).get("confidence"), 0.0),
        ),
        reverse=True,
    )

    return blocks


# ---------------------------------------------------
# EPISODE CONTEXT
# ---------------------------------------------------

def build_episode_context(view: Dict[str, Any], dialogue_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    overview = safe_dict(view.get("overview"))
    top_stories = safe_list(view.get("top_stories"))
    featured_items = safe_dict(view.get("featured_items"))
    anchor_enrichment = safe_dict(view.get("anchor_enrichment"))
    vertical_opportunities = safe_list(view.get("vertical_opportunities"))

    domain_counts: Dict[str, int] = {}
    dominant_assets: List[str] = []
    numeric_hooks: List[str] = []
    callback_threads: List[str] = []
    top_lines: List[str] = []
    signal_types: List[str] = []
    candidate_anchors: List[str] = []

    risk_constructive = 0
    risk_fragile = 0

    for block in dialogue_blocks:
        domain = clean(block.get("domain") or "general")
        domain_counts[domain] = domain_counts.get(domain, 0) + 1

        for entity in safe_list(block.get("entities")):
            entity = clean(entity)
            if entity and entity not in dominant_assets:
                dominant_assets.append(entity)

        pd_hints = safe_dict(block.get("pd_hints"))
        hook = clean(pd_hints.get("numeric_hook"))
        if hook:
            numeric_hooks.append(hook)

        thread_id = clean(pd_hints.get("thread_id"))
        if thread_id:
            callback_threads.append(thread_id)

        for turn in safe_list(block.get("dialogue")):
            turn = safe_dict(turn)
            text = clean(turn.get("text"))
            if text:
                top_lines.append(text)

                lowered = text.lower()
                bearish_terms = ["fragile", "pressure", "stress", "risk", "liquidation", "breakdown", "lower"]
                bullish_terms = ["accumulation", "breakout", "bullish", "recovery", "expansion", "inflow", "strong"]

                risk_fragile += sum(1 for t in bearish_terms if t in lowered)
                risk_constructive += sum(1 for t in bullish_terms if t in lowered)

        context = safe_dict(block.get("context"))
        stype = clean(context.get("signal_type"))
        if stype:
            signal_types.append(stype)

        for anchor in safe_list(block.get("anchor_candidates")):
            anchor = clean(anchor)
            if anchor:
                candidate_anchors.append(anchor)

    dominant_domain = max(domain_counts, key=domain_counts.get) if domain_counts else "general"

    if risk_fragile > risk_constructive:
        risk_direction = "fragile"
    elif risk_constructive > risk_fragile:
        risk_direction = "constructive"
    else:
        risk_direction = "mixed"

    total_signals = safe_int(overview.get("total_signals"), 0)
    unique_entities = safe_int(overview.get("unique_entities"), 0)
    source_count = safe_int(overview.get("source_count"), 0)

    signal_summary = (
        f"{total_signals} signals processed across {source_count} sources and "
        f"{unique_entities} entities."
    )

    if domain_counts.get("culture", 0) > 0 and dominant_domain == "culture":
        culture_summary = "Retail sentiment and culture are central to the episode."
    elif domain_counts.get("culture", 0) > 0:
        culture_summary = "Retail culture is present, but not the primary driver."
    else:
        culture_summary = "Culture is secondary in this episode."

    narrative_summary = safe_dict(anchor_enrichment.get("narrative_summary"))
    primary_title = clean(narrative_summary.get("primary_title"))
    lead_titles = [
        clean(item.get("title"))
        for item in safe_list(anchor_enrichment.get("lead_angles"))[:3]
        if clean(safe_dict(item).get("title"))
    ]

    top_story_titles = [
        clean(item.get("title"))
        for item in top_stories[:5]
        if clean(safe_dict(item).get("title"))
    ]

    episode_thesis_parts = []
    if primary_title:
        episode_thesis_parts.append(primary_title)
    episode_thesis_parts.extend([t for t in lead_titles if t not in episode_thesis_parts])

    if not episode_thesis_parts:
        episode_thesis_parts.extend(top_story_titles[:3])

    if episode_thesis_parts:
        episode_thesis = " | ".join(episode_thesis_parts[:3])
    else:
        episode_thesis = "Cross-domain market movement is being shaped by signal alignment and narrative rotation."

    featured_verticals = [
        clean(v.get("vertical"))
        for v in vertical_opportunities
        if clean(safe_dict(v).get("vertical"))
    ][:6]

    featured_items_out = {
        "memecoin_of_the_day": safe_dict(featured_items.get("memecoin_of_the_day")),
        "culture_rotation": safe_dict(featured_items.get("culture_rotation")),
        "macro_news": safe_dict(featured_items.get("macro_news")),
    }

    return {
        "episode_thesis": episode_thesis,
        "signal_summary": signal_summary,
        "dominant_assets": dominant_assets[:8],
        "dominant_domain": dominant_domain,
        "domain_counts": domain_counts,
        "risk_direction": risk_direction,
        "culture_summary": culture_summary,
        "callback_threads": unique_preserve(callback_threads)[:6],
        "numeric_hooks": unique_preserve(numeric_hooks)[:6],
        "top_lines": unique_preserve(top_lines)[:6],
        "top_story_titles": top_story_titles,
        "featured_verticals": featured_verticals,
        "featured_items": featured_items_out,
        "priority_signal_types": unique_preserve(signal_types)[:12],
        "anchor_candidates": unique_preserve(candidate_anchors)[:8],
        "timestamp": now_ts(),
        "source": "toknclaw",
    }


# ---------------------------------------------------
# PROMO PAYLOAD
# ---------------------------------------------------

def choose_promo_type(domain: str, signal_type: str) -> str:
    d = clean(domain).lower()
    s = clean(signal_type).lower()

    if d == "macro":
        return "top_movers_today"
    if d == "onchain":
        return "whale_alert"
    if d == "culture":
        return "sentiment_scan"
    if d == "defi":
        return "liquidity_watch"
    if d == "regulation":
        return "breaking_news"
    if "large_token_transfer" in s:
        return "whale_alert"

    return "breaking_news"


def build_promo_queue(view: Dict[str, Any]) -> List[Dict[str, Any]]:
    stories = safe_list(view.get("top_stories"))
    out: List[Dict[str, Any]] = []

    for idx, story in enumerate(stories[:8]):
        story = safe_dict(story)

        domain = clean(story.get("domain"))
        signal_type = clean(story.get("signal_type"))
        title = clean(story.get("title"))
        summary = clean(story.get("summary"))
        entity = clean(story.get("entity"))

        if not title and not summary:
            continue

        out.append({
            "promo_rank": idx + 1,
            "promo_type": choose_promo_type(domain, signal_type),
            "domain": normalize_domain(domain),
            "raw_domain": domain,
            "signal_type": signal_type,
            "headline": title,
            "summary": summary,
            "entity": entity,
            "confidence": safe_float(story.get("confidence"), 0.0),
            "sentiment_score": safe_float(story.get("sentiment_score"), 0.0),
            "story_score": safe_float(story.get("story_score"), 0.0),
            "raw_url": story.get("raw_url"),
        })

    return out


def build_promo_payload(view: Dict[str, Any], dialogue_blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    promo_queue = build_promo_queue(view)
    primary = promo_queue[0] if promo_queue else {}

    primary_domain = clean(primary.get("domain"))
    primary_signal_type = clean(primary.get("signal_type"))
    primary_entity = clean(primary.get("entity"))
    headline = clean(primary.get("headline"))
    summary = clean(primary.get("summary"))

    hooks: List[str] = []

    if headline:
        hooks.append(headline)

    if summary:
        hooks.append(summary)

    if primary_domain == "macro":
        hooks.append("Macro pressure is shaping the next move.")
    elif primary_domain == "markets":
        hooks.append("Price structure and positioning are telling the story.")
    elif primary_domain == "defi":
        hooks.append("Capital is concentrating where protocol activity is strongest.")
    elif primary_domain == "culture":
        hooks.append("Retail mood is becoming part of the market signal.")
    elif primary_domain == "onchain":
        hooks.append("Flow is moving before broad consensus catches up.")
    elif primary_domain == "regulation":
        hooks.append("Policy pressure can reprice the market quickly.")

    featured_items = safe_dict(view.get("featured_items"))
    macro_news = safe_dict(featured_items.get("macro_news"))
    memecoin_of_day = safe_dict(featured_items.get("memecoin_of_the_day"))

    facts = {
        "primary_domain": primary_domain or "general",
        "primary_signal_type": primary_signal_type,
        "primary_entity": primary_entity,
        "promo_queue_size": len(promo_queue),
        "top_domains": unique_preserve([
            clean(block.get("domain"))
            for block in dialogue_blocks
            if clean(block.get("domain"))
        ])[:6],
        "featured_macro_title": clean(macro_news.get("title")),
        "featured_memecoin_title": clean(memecoin_of_day.get("title")),
    }

    supporting_context = {
        "domain": primary_domain or "general",
        "signal_type": primary_signal_type,
        "entities": [primary_entity] if primary_entity else [],
        "dialogue_block_count": len(dialogue_blocks),
        "anchor_candidates": unique_preserve([
            clean(a)
            for block in dialogue_blocks[:5]
            for a in safe_list(block.get("anchor_candidates"))
            if clean(a)
        ])[:6],
    }

    return {
        "promo_category": "signal",
        "promo_type": clean(primary.get("promo_type")) or "breaking_news",
        "anchor": None,
        "anchor_candidates": supporting_context["anchor_candidates"],
        "emotion": "confident",
        "intensity": 0.7,
        "length_sec": 30,
        "top_news": True,
        "headline": headline,
        "summary": summary,
        "timestamp": now_ts(),
        "source": "toknclaw",
        "facts": facts,
        "hooks": unique_preserve([clean(h) for h in hooks if clean(h)])[:6],
        "promo_queue": promo_queue,
        "supporting_context": supporting_context,
        "featured_items": {
            "macro_news": macro_news,
            "memecoin_of_the_day": memecoin_of_day,
        },
    }


# ---------------------------------------------------
# MAIN
# ---------------------------------------------------

def run() -> None:
    view, source_path = load_media_view()

    dialogue_blocks = build_dialogue_blocks(view)
    episode_context = build_episode_context(view, dialogue_blocks)
    promo_payload = build_promo_payload(view, dialogue_blocks)

    write_json_atomic(OUTPUT_DIALOGUE, TMP_DIALOGUE, dialogue_blocks)
    write_json_atomic(OUTPUT_CONTEXT, TMP_CONTEXT, episode_context)
    write_json_atomic(OUTPUT_PROMO, TMP_PROMO, promo_payload)

    print(f"[INGEST ADAPTER] media_view={source_path}")
    print(f"[INGEST ADAPTER] blocks={len(dialogue_blocks)}")
    print(f"[INGEST ADAPTER] domains={unique_preserve([clean(b.get('domain')) for b in dialogue_blocks])}")
    print(f"[INGEST ADAPTER] context_ready")
    print(f"[INGEST ADAPTER] promo_ready")


if __name__ == "__main__":
    run()
