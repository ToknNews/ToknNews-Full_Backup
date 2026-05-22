#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS ASSEMBLY ENGINE
Timeline Builder v7 (Clean)

Purpose
-------
Assembles final broadcast timeline from executed roundtable.

Inputs
------
/opt/toknnews/data/broadcast/broadcast_roundtable.json

Outputs
-------
/opt/toknnews/data/timeline.json

Design Rules
------------
• NO content generation
• NO logic injection
• Pure assembly layer
• Preserve ordering
• Prepare for TTS + render

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

INPUT_PATH = Path("/opt/toknnews/data/broadcast/broadcast_roundtable.json")
OUTPUT_PATH = Path("/opt/toknnews/data/timeline.json")
TMP_PATH = OUTPUT_PATH.with_suffix(".tmp")

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def now_ts():
    return time.time()

def atomic_write(path: Path, tmp: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(path)

# ---------------------------------------------------------
# CORE
# ---------------------------------------------------------

def build_timeline(roundtable: Dict[str, Any]) -> Dict[str, Any]:

    turns = roundtable.get("timeline", [])

    timeline: List[Dict[str, Any]] = []

    for t in turns:
        timeline.append({
            "speaker": clean(t.get("speaker")),
            "text": clean(t.get("text")),
            "intent_type": clean(t.get("intent_type")),
            "domain": clean(t.get("story_ref", {}).get("domain")),
            "entity": clean(t.get("story_ref", {}).get("resolved_entity")),
            "raw_url": clean(t.get("story_ref", {}).get("raw_url"))
        })

    return {
        "generated_at": now_ts(),
        "meta": {
            "total_lines": len(timeline),
            "acts": len(set([t["domain"] for t in timeline if t.get("domain")])),
        },
        "timeline": timeline
    }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing broadcast_roundtable.json")

    roundtable = json.loads(INPUT_PATH.read_text())

    timeline = build_timeline(roundtable)

    atomic_write(OUTPUT_PATH, TMP_PATH, timeline)

    print(f"[TIMELINE] lines={len(timeline['timeline'])}")
    print(f"[TIMELINE] acts={timeline['meta']['acts']}")

if __name__ == "__main__":
    main()
