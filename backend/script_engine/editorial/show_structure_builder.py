#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝

TOKNNEWS EDITORIAL ENGINE
Show Structure Builder

Purpose
-------
Transforms raw ToknClaw media_view into a structured broadcast spine.

This module is the FIRST stage of show construction and defines:
• what stories make the show
• how they are grouped (acts)
• which domains matter most
• where meme / Bitsy content comes from
• what URLs should be enriched downstream

Primary Input
-------------
/opt/toknnews/data/media_view.json

Primary Output
--------------
/opt/toknnews/data/show_structure.json

Design Rules
------------
• Deterministic only (NO LLM usage)
• No dialogue generation
• No narrative invention
• Preserve all critical metadata
• Normalize domain classification
• Promote memecoin / pump.fun into "meme" domain
• Provide clean contracts for downstream modules

Author: TOKN Systems
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

INPUT_PATH = Path("/opt/toknnews/data/media_view.json")
OUTPUT_PATH = Path("/opt/toknnews/data/show_structure.json")
TMP_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".tmp")

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

MIN_STORY_SCORE = 10.0
MAX_STORIES_PER_DOMAIN = 4

DOMAIN_PRIORITY = [
    "macro",
    "crypto_major",
    "defi",
    "news",
    "crypto_alt",
    "meme",
    "regulation"
]

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def safe_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []

def safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return default

def now_ts() -> float:
    return time.time()

def atomic_write(path: Path, tmp: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)

# ---------------------------------------------------------
# DOMAIN NORMALIZATION
# ---------------------------------------------------------

def normalize_domain(story: Dict[str, Any]) -> str:
    domain = clean(story.get("domain")).lower()
    signal_type = clean(story.get("signal_type")).lower()
    title = clean(story.get("title")).lower()

    # Meme override logic
    if "pump" in signal_type or "pump.fun" in title or "memecoin" in signal_type:
        return "meme"

    return domain or "unknown"

# ---------------------------------------------------------
# ENTITY CLASSIFICATION
# ---------------------------------------------------------

def classify_entity(entity: str) -> str:
    e = entity.upper()

    if e in ["BTC", "ETH", "SOL"]:
        return "major"

    if len(e) > 20:
        return "contract"

    if "PUMP" in e:
        return "memecoin"

    return "general"

# ---------------------------------------------------------
# FILTERING
# ---------------------------------------------------------

def is_valid_story(story: Dict[str, Any]) -> bool:
    return safe_float(story.get("story_score")) >= MIN_STORY_SCORE

# ---------------------------------------------------------
# GROUPING
# ---------------------------------------------------------

def group_by_domain(stories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}

    for s in stories:
        domain = normalize_domain(s)
        out.setdefault(domain, []).append(s)

    return out

# ---------------------------------------------------------
# SORTING
# ---------------------------------------------------------

def sort_stories(stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return sorted(
        stories,
        key=lambda x: safe_float(x.get("story_score")),
        reverse=True
    )

# ---------------------------------------------------------
# ACT BUILDER
# ---------------------------------------------------------

def build_act(domain: str, stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    stories = sort_stories(stories)[:MAX_STORIES_PER_DOMAIN]

    return {
        "type": f"{domain}_act",
        "domain": domain,
        "tone": domain,
        "stories": [
            {
                "title": clean(s.get("title")),
                "summary": clean(s.get("summary")),
                "entity": clean(s.get("entity")),
                "entity_type": classify_entity(clean(s.get("entity"))),
                "signal_type": clean(s.get("signal_type")),
                "score": safe_float(s.get("story_score")),
                "confidence": safe_float(s.get("confidence")),
                "raw_url": clean(s.get("raw_url")),
            }
            for s in stories
        ]
    }

# ---------------------------------------------------------
# BITSY SEGMENT
# ---------------------------------------------------------

def build_bitsy_segment(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    meme_candidates = [
        s for s in stories
        if normalize_domain(s) == "meme"
    ]

    meme_candidates = sort_stories(meme_candidates)[:5]

    return {
        "type": "bitsy_chaos_segment",
        "stories": [
            {
                "title": clean(s.get("title")),
                "entity": clean(s.get("entity")),
                "summary": clean(s.get("summary")),
                "score": safe_float(s.get("story_score")),
            }
            for s in meme_candidates
        ]
    }

# ---------------------------------------------------------
# FETCH TARGETS
# ---------------------------------------------------------

def build_fetch_targets(stories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    targets = []

    for s in stories:
        url = clean(s.get("raw_url"))
        if not url:
            continue

        targets.append({
            "url": url,
            "entity": clean(s.get("entity")),
            "domain": normalize_domain(s),
            "source": "story_raw_url"
        })

    return targets[:15]

# ---------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------

def build_show_structure(media_view: Dict[str, Any]) -> Dict[str, Any]:
    raw_stories = safe_list(media_view.get("top_stories"))

    filtered = [s for s in raw_stories if is_valid_story(s)]
    grouped = group_by_domain(filtered)

    acts: List[Dict[str, Any]] = []

    for domain in DOMAIN_PRIORITY:
        if domain not in grouped:
            continue

        act = build_act(domain, grouped[domain])
        if act["stories"]:
            acts.append(act)

    return {
        "generated_at": now_ts(),
        "view_name": clean(media_view.get("view_name")),
        "acts": acts,
        "bitsy_segment": build_bitsy_segment(filtered),
        "fetch_targets": build_fetch_targets(filtered),
        "meta": {
            "total_input_stories": len(raw_stories),
            "total_filtered_stories": len(filtered),
            "act_count": len(acts),
        }
    }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input: {INPUT_PATH}")

    media_view = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    show_structure = build_show_structure(media_view)

    atomic_write(OUTPUT_PATH, TMP_OUTPUT_PATH, show_structure)

    print(f"[SHOW STRUCTURE] acts={len(show_structure.get('acts', []))}")
    print(f"[SHOW STRUCTURE] bitsy_items={len(show_structure.get('bitsy_segment', {}).get('stories', []))}")
    print(f"[SHOW STRUCTURE] fetch_targets={len(show_structure.get('fetch_targets', []))}")

if __name__ == "__main__":
    main()
