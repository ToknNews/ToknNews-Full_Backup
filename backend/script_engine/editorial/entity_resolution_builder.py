#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝

TOKNNEWS ENRICHMENT ENGINE
Entity Resolution Builder

Purpose
-------
Builds a deterministic entity resolution map for ToknNews.

This module converts raw story entities into broadcast-safe labels and
structured metadata for downstream use by:
• story_context_builder
• conductor_v2
• anchor prompts
• TTS cleanup
• render metadata

Primary Input
-------------
/opt/toknnews/data/show_structure.json

Primary Output
--------------
/opt/toknnews/data/entity_resolution_map.json

Design Rules
------------
• Deterministic only
• No web fetches
• No LLM usage
• Preserve raw entity values
• Produce clean broadcast labels
• Classify majors, protocols, macro symbols, contracts, memes
• Prevent anchors from speaking raw addresses whenever possible

Author: TOKN Systems
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Set

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

INPUT_PATH = Path("/opt/toknnews/data/show_structure.json")
OUTPUT_PATH = Path("/opt/toknnews/data/entity_resolution_map.json")
TMP_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".tmp")

# ---------------------------------------------------------
# CANONICAL LABEL MAPS
# ---------------------------------------------------------

KNOWN_ENTITY_MAP: Dict[str, Dict[str, Any]] = {
    "BTC": {
        "entity_class": "major",
        "display_label": "Bitcoin",
        "spoken_label": "Bitcoin",
        "short_label": "BTC",
        "confidence": 1.0,
    },
    "ETH": {
        "entity_class": "major",
        "display_label": "Ethereum",
        "spoken_label": "Ethereum",
        "short_label": "ETH",
        "confidence": 1.0,
    },
    "SOL": {
        "entity_class": "major",
        "display_label": "Solana",
        "spoken_label": "Solana",
        "short_label": "SOL",
        "confidence": 1.0,
    },
    "BNB": {
        "entity_class": "major",
        "display_label": "BNB",
        "spoken_label": "Binance Coin",
        "short_label": "BNB",
        "confidence": 1.0,
    },
    "XRP": {
        "entity_class": "major",
        "display_label": "XRP",
        "spoken_label": "X R P",
        "short_label": "XRP",
        "confidence": 1.0,
    },
    "USDT": {
        "entity_class": "stablecoin",
        "display_label": "Tether",
        "spoken_label": "Tether",
        "short_label": "USDT",
        "confidence": 1.0,
    },
    "USDC": {
        "entity_class": "stablecoin",
        "display_label": "USD Coin",
        "spoken_label": "USD Coin",
        "short_label": "USDC",
        "confidence": 1.0,
    },
    "AAVE": {
        "entity_class": "protocol",
        "display_label": "Aave",
        "spoken_label": "Aave",
        "short_label": "AAVE",
        "confidence": 1.0,
    },
    "AAVE V3": {
        "entity_class": "protocol",
        "display_label": "Aave V3",
        "spoken_label": "Aave V3",
        "short_label": "AAVE V3",
        "confidence": 1.0,
    },
    "UNI": {
        "entity_class": "protocol",
        "display_label": "Uniswap",
        "spoken_label": "Uniswap",
        "short_label": "UNI",
        "confidence": 1.0,
    },
    "BINANCE CEX": {
        "entity_class": "exchange",
        "display_label": "Binance",
        "spoken_label": "Binance",
        "short_label": "BINANCE",
        "confidence": 1.0,
    },
    "SP500": {
        "entity_class": "macro_index",
        "display_label": "S&P 500",
        "spoken_label": "the S and P 500",
        "short_label": "SP500",
        "confidence": 1.0,
    },
    "VIXCLS": {
        "entity_class": "macro_index",
        "display_label": "VIX",
        "spoken_label": "the VIX",
        "short_label": "VIX",
        "confidence": 1.0,
    },
    "DGS2": {
        "entity_class": "macro_rate",
        "display_label": "US 2Y Treasury Yield",
        "spoken_label": "the two year yield",
        "short_label": "US 2Y",
        "confidence": 1.0,
    },
    "NEWS": {
        "entity_class": "narrative_bucket",
        "display_label": "General News",
        "spoken_label": "the broader crypto narrative",
        "short_label": "NEWS",
        "confidence": 0.9,
    },
}

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def now_ts() -> float:
    return time.time()


def atomic_write_json(path: Path, tmp_path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp_path.replace(path)


def looks_like_evm_address(value: str) -> bool:
    return bool(re.fullmatch(r"0x[a-fA-F0-9]{40}", clean(value)))


def looks_like_long_contractish_token(value: str) -> bool:
    raw = clean(value)
    if not raw:
        return False

    # Solana/pump.fun-like ids are usually long base58-ish strings.
    if len(raw) >= 24 and re.fullmatch(r"[A-Za-z0-9]+", raw):
        return True

    return False


def shorten_contract(value: str, head: int = 6, tail: int = 4) -> str:
    raw = clean(value)
    if len(raw) <= head + tail + 3:
        return raw
    return f"{raw[:head]}...{raw[-tail:]}"


def detect_meme_hint(entity: str, story_title: str, story_summary: str, signal_type: str, domain: str) -> bool:
    blob = " | ".join(
        [
            clean(entity).lower(),
            clean(story_title).lower(),
            clean(story_summary).lower(),
            clean(signal_type).lower(),
            clean(domain).lower(),
        ]
    )

    meme_terms = [
        "pump.fun",
        "pumpfun",
        "pump",
        "memecoin",
        "funny_name",
        "alpha entry signal",
        "solana alpha entry signal",
        "chaos",
    ]
    return any(term in blob for term in meme_terms)


def infer_entity_class(
    entity: str,
    entity_type: str,
    domain: str,
    signal_type: str,
    title: str,
    summary: str,
) -> str:
    raw = clean(entity)
    typed = clean(entity_type).lower()
    domain = clean(domain).lower()
    signal_type = clean(signal_type).lower()

    if raw.upper() in KNOWN_ENTITY_MAP:
        return clean(KNOWN_ENTITY_MAP[raw.upper()].get("entity_class"))

    if typed in {"major", "stablecoin", "protocol", "exchange", "macro_index", "macro_rate"}:
        return typed

    if detect_meme_hint(raw, title, summary, signal_type, domain):
        return "memecoin"

    if looks_like_evm_address(raw) or looks_like_long_contractish_token(raw):
        return "contract"

    if domain == "macro":
        return "macro_generic"

    if domain == "defi":
        return "protocol"

    if domain == "meme":
        return "memecoin"

    if domain == "crypto_alt":
        return "altcoin"

    if domain == "crypto_major":
        return "major"

    return "general"


def infer_display_and_spoken_labels(
    entity: str,
    entity_class: str,
    signal_type: str,
    title: str,
    summary: str,
) -> Dict[str, str]:
    raw = clean(entity)
    upper = raw.upper()

    if upper in KNOWN_ENTITY_MAP:
        row = KNOWN_ENTITY_MAP[upper]
        return {
            "display_label": clean(row.get("display_label")),
            "spoken_label": clean(row.get("spoken_label")),
            "short_label": clean(row.get("short_label")),
        }

    if entity_class == "memecoin":
        short = shorten_contract(raw, head=8, tail=0).replace("...", "")
        display = short if short else "Unknown Meme Token"
        spoken = f"the token {short}" if short else "an unresolved meme token"
        return {
            "display_label": display,
            "spoken_label": spoken,
            "short_label": short or raw,
        }

    if entity_class == "contract":
        short = shorten_contract(raw)
        return {
            "display_label": short,
            "spoken_label": f"the contract {short}",
            "short_label": short,
        }

    if entity_class == "protocol":
        nice = raw.title() if raw.isupper() is False else raw
        return {
            "display_label": nice,
            "spoken_label": nice,
            "short_label": nice,
        }

    if entity_class == "macro_generic":
        nice = raw.replace("_", " ").title()
        return {
            "display_label": nice or "Macro Signal",
            "spoken_label": nice or "the macro signal",
            "short_label": nice or raw,
        }

    nice = raw.title() if raw and raw.isupper() is False else raw
    return {
        "display_label": nice or raw,
        "spoken_label": nice or raw,
        "short_label": nice or raw,
    }


def infer_confidence(entity: str, entity_class: str) -> float:
    upper = clean(entity).upper()

    if upper in KNOWN_ENTITY_MAP:
        return float(KNOWN_ENTITY_MAP[upper].get("confidence", 1.0))

    if entity_class in {"memecoin", "contract"}:
        return 0.6

    if entity_class in {"protocol", "altcoin", "macro_generic"}:
        return 0.8

    return 0.7


# ---------------------------------------------------------
# EXTRACTION
# ---------------------------------------------------------

def collect_story_entities(show_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for act in safe_list(show_structure.get("acts")):
        act = safe_dict(act)
        domain = clean(act.get("domain"))

        for story in safe_list(act.get("stories")):
            story = safe_dict(story)
            rows.append(
                {
                    "entity": clean(story.get("entity")),
                    "entity_type": clean(story.get("entity_type")),
                    "domain": domain,
                    "signal_type": clean(story.get("signal_type")),
                    "title": clean(story.get("title")),
                    "summary": clean(story.get("summary")),
                    "raw_url": clean(story.get("raw_url")),
                }
            )

    return rows


# ---------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------

def build_resolution_row(row: Dict[str, Any]) -> Dict[str, Any]:
    entity = clean(row.get("entity"))
    entity_type = clean(row.get("entity_type"))
    domain = clean(row.get("domain"))
    signal_type = clean(row.get("signal_type"))
    title = clean(row.get("title"))
    summary = clean(row.get("summary"))

    entity_class = infer_entity_class(
        entity=entity,
        entity_type=entity_type,
        domain=domain,
        signal_type=signal_type,
        title=title,
        summary=summary,
    )

    labels = infer_display_and_spoken_labels(
        entity=entity,
        entity_class=entity_class,
        signal_type=signal_type,
        title=title,
        summary=summary,
    )

    return {
        "raw_entity": entity,
        "entity_class": entity_class,
        "display_label": clean(labels.get("display_label")),
        "spoken_label": clean(labels.get("spoken_label")),
        "short_label": clean(labels.get("short_label")),
        "raw_passthrough": entity,
        "is_contract_like": looks_like_evm_address(entity) or looks_like_long_contractish_token(entity),
        "is_meme_candidate": detect_meme_hint(entity, title, summary, signal_type, domain),
        "confidence": infer_confidence(entity, entity_class),
        "source_hints": {
            "domain": domain,
            "signal_type": signal_type,
            "title": title,
            "raw_url": clean(row.get("raw_url")),
        },
    }


def build_entity_resolution_map(show_structure: Dict[str, Any]) -> Dict[str, Any]:
    rows = collect_story_entities(show_structure)

    by_entity: Dict[str, Dict[str, Any]] = {}
    seen: Set[str] = set()

    for row in rows:
        entity = clean(row.get("entity"))
        if not entity:
            continue

        if entity in seen:
            continue

        seen.add(entity)
        by_entity[entity] = build_resolution_row(row)

    ordered_entities = sorted(by_entity.keys(), key=lambda x: x.lower())

    return {
        "generated_at": now_ts(),
        "source_view": clean(show_structure.get("view_name")),
        "entity_count": len(ordered_entities),
        "entities": {entity: by_entity[entity] for entity in ordered_entities},
        "meta": {
            "input_story_count": len(rows),
            "known_entity_hits": len([e for e in ordered_entities if e.upper() in KNOWN_ENTITY_MAP]),
            "contract_like_count": len(
                [e for e in ordered_entities if safe_dict(by_entity.get(e)).get("is_contract_like")]
            ),
            "meme_candidate_count": len(
                [e for e in ordered_entities if safe_dict(by_entity.get(e)).get("is_meme_candidate")]
            ),
        },
    }


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input file: {INPUT_PATH}")

    show_structure = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    payload = build_entity_resolution_map(show_structure)

    atomic_write_json(OUTPUT_PATH, TMP_OUTPUT_PATH, payload)

    print(f"[ENTITY RESOLUTION] input={INPUT_PATH}")
    print(f"[ENTITY RESOLUTION] output={OUTPUT_PATH}")
    print(f"[ENTITY RESOLUTION] entity_count={payload.get('entity_count', 0)}")
    print(f"[ENTITY RESOLUTION] contract_like={safe_dict(payload.get('meta')).get('contract_like_count', 0)}")
    print(f"[ENTITY RESOLUTION] meme_candidates={safe_dict(payload.get('meta')).get('meme_candidate_count', 0)}")


if __name__ == "__main__":
    main()
