#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝

TOKNNEWS EDITORIAL ENGINE
Show Director

Purpose
-------
Transforms structured story acts into a fully planned broadcast.

This module defines:
• show flow
• act sequencing
• anchor roles
• debate vs analysis
• pacing
• Bitsy + Vega placement

Primary Input
-------------
/opt/toknnews/data/show_structure.json

Primary Output
--------------
/opt/toknnews/data/show_director.json

Design Rules
------------
• Deterministic (NO LLM)
• No dialogue generation
• No hallucinated data
• Only orchestration decisions
• Clean contract for conductor + host layer

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

INPUT_PATH = Path("/opt/toknnews/data/show_structure.json")
OUTPUT_PATH = Path("/opt/toknnews/data/show_director.json")
TMP_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".tmp")

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

MAX_STORIES_PER_ACT = 4

# Anchor mapping by domain
DOMAIN_ANCHOR_MAP = {
    "macro": ("bond", "cash"),
    "crypto_major": ("ledger", "bond"),
    "defi": ("reef", "ledger"),
    "news": ("ivy", "bond"),
    "crypto_alt": ("cash", "lawson"),
    "meme": ("cash", "lawson"),
    "regulation": ("lawson", "ivy"),
}

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def safe_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []

def now_ts() -> float:
    return time.time()

def atomic_write(path: Path, tmp: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)

# ---------------------------------------------------------
# ANCHOR LOGIC
# ---------------------------------------------------------

def get_anchor_roles(domain: str) -> Dict[str, str]:
    domain = clean(domain).lower()

    lead, counter = DOMAIN_ANCHOR_MAP.get(domain, ("bond", "cash"))

    return {
        "lead": lead,
        "counter": counter,
        "support": "chip"
    }

# ---------------------------------------------------------
# STORY PLANNER
# ---------------------------------------------------------

def build_story_plan(story: Dict[str, Any], domain: str) -> Dict[str, Any]:
    roles = get_anchor_roles(domain)

    signal_type = clean(story.get("signal_type")).lower()

    # Determine segment type
    if "indicator" in signal_type:
        segment_type = "analysis"
    elif "transfer" in signal_type:
        segment_type = "flow_read"
    elif domain == "meme":
        segment_type = "chaos"
    else:
        segment_type = "debate"

    return {
        "title": clean(story.get("title")),
        "entity": clean(story.get("entity")),
        "summary": clean(story.get("summary")),
        "signal_type": signal_type,
        "raw_url": clean(story.get("raw_url")),

        "segment_type": segment_type,
        "debate": segment_type == "debate",

        "anchor_roles": roles,

        "editorial_flags": {
            "needs_context": True,
            "allow_bitsy": domain == "meme",
            "priority": "high" if segment_type == "debate" else "medium"
        }
    }

# ---------------------------------------------------------
# ACT PLANNER
# ---------------------------------------------------------

def build_act_plan(act: Dict[str, Any], index: int) -> Dict[str, Any]:
    domain = clean(act.get("domain")).lower()
    stories = safe_list(act.get("stories"))[:MAX_STORIES_PER_ACT]

    return {
        "act_index": index,
        "domain": domain,
        "type": clean(act.get("type")),
        "tone": clean(act.get("tone")),

        "structure": {
            "intro_required": True,
            "debate_density": sum(1 for s in stories if "news" in clean(s.get("signal_type")).lower()),
        },

        "stories": [
            build_story_plan(story, domain)
            for story in stories
        ]
    }

# ---------------------------------------------------------
# BITSY + VEGA LOGIC
# ---------------------------------------------------------

def build_bitsy_plan(bitsy_segment: Dict[str, Any]) -> Dict[str, Any]:
    stories = safe_list(bitsy_segment.get("stories"))

    return {
        "enabled": len(stories) > 0,
        "stories": stories[:2],
        "mode": "endcap"  # final chaos segment
    }

def build_vega_plan() -> Dict[str, Any]:
    return {
        "enabled": True,
        "use_intro": True,
        "use_outro": True
    }

# ---------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------

def build_show_director(show_structure: Dict[str, Any]) -> Dict[str, Any]:
    acts = safe_list(show_structure.get("acts"))

    planned_acts = [
        build_act_plan(act, i)
        for i, act in enumerate(acts)
    ]

    return {
        "generated_at": now_ts(),

        "show_flow": {
            "act_count": len(planned_acts),
            "structure": "linear_broadcast"
        },

        "acts": planned_acts,

        "bitsy_plan": build_bitsy_plan(show_structure.get("bitsy_segment", {})),
        "vega_plan": build_vega_plan(),

        "meta": {
            "source_view": clean(show_structure.get("view_name")),
            "total_acts": len(planned_acts),
        }
    }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing input: {INPUT_PATH}")

    show_structure = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    show_director = build_show_director(show_structure)

    atomic_write(OUTPUT_PATH, TMP_OUTPUT_PATH, show_director)

    print(f"[SHOW DIRECTOR] acts={len(show_director.get('acts', []))}")
    print(f"[SHOW DIRECTOR] bitsy_enabled={show_director.get('bitsy_plan', {}).get('enabled')}")
    print(f"[SHOW DIRECTOR] vega_enabled={show_director.get('vega_plan', {}).get('enabled')}")

if __name__ == "__main__":
    main()
