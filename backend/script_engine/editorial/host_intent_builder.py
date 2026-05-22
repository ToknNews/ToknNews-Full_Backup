#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝

TOKNNEWS EDITORIAL ENGINE
Host Intent Builder

Purpose
-------
Defines host behavior for ToknNews without generating spoken lines.

This module outputs structured Chip + Vega intent that drives:
• anchor prompts
• conversation flow
• debate structure
• transitions
• Bitsy chaos placement

Primary Inputs
--------------
/opt/toknnews/data/show_structure.json
/opt/toknnews/data/show_director.json

Primary Output
--------------
/opt/toknnews/data/host_intents.json

Design Rules
------------
• Deterministic
• No spoken dialogue generation
• No repetition templates
• Encodes behavior, not language
• Drives conductor, not replaces it

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

SHOW_STRUCTURE_PATH = Path("/opt/toknnews/data/show_structure.json")
SHOW_DIRECTOR_PATH = Path("/opt/toknnews/data/show_director.json")
OUTPUT_PATH = Path("/opt/toknnews/data/host_intents.json")
TMP_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".tmp")

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def safe_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []

def safe_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}

def now_ts() -> float:
    return time.time()

def atomic_write(path: Path, tmp: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)

# ---------------------------------------------------------
# CHIP PERSONALITY MODEL
# ---------------------------------------------------------

CHIP_PROFILE = {
    "tone": "calm_authoritative",
    "style": "analytical",
    "behavior_rules": [
        "asks before explaining",
        "summarizes after debate",
        "pushes clarity over hype",
        "redirects when needed",
        "never repeats phrasing"
    ]
}

# ---------------------------------------------------------
# INTENT BUILDERS
# ---------------------------------------------------------

def show_open_intent(structure: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "show_open",
        "speaker": "chip",
        "mode": "frame",
        "goal": "set_board",
        "targets": [],
    }

def vega_intro_intent() -> Dict[str, Any]:
    return {
        "type": "vega_intro",
        "speaker": "vega",
        "mode": "identity",
        "goal": "open_show",
    }

def vega_outro_intent() -> Dict[str, Any]:
    return {
        "type": "vega_outro",
        "speaker": "vega",
        "mode": "identity",
        "goal": "close_show",
    }

def act_intro_intent(act: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "act_intro",
        "speaker": "chip",
        "mode": "frame",
        "goal": "introduce_domain",
        "domain": clean(act.get("domain")),
    }

def question_intent(anchor: str, story: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "question",
        "speaker": "chip",
        "mode": "probe",
        "goal": "extract_analysis",
        "target_anchor": anchor,
        "entity": clean(story.get("entity")),
        "topic": clean(story.get("title")),
    }

def challenge_intent(anchor: str, story: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "type": "challenge",
        "speaker": "chip",
        "mode": "challenge",
        "goal": "increase_tension",
        "target_anchor": anchor,
        "entity": clean(story.get("entity")),
    }

def bridge_intent(next_domain: str) -> Dict[str, Any]:
    return {
        "type": "transition",
        "speaker": "chip",
        "mode": "bridge",
        "goal": "move_segment",
        "next_domain": next_domain
    }

def bitsy_toss_intent() -> Dict[str, Any]:
    return {
        "type": "bitsy_toss",
        "speaker": "chip",
        "mode": "handoff",
        "goal": "inject_chaos"
    }

def show_close_intent() -> Dict[str, Any]:
    return {
        "type": "show_close",
        "speaker": "chip",
        "mode": "synthesize",
        "goal": "wrap_show"
    }

# ---------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------

def build_host_intents(structure: Dict[str, Any], director: Dict[str, Any]) -> Dict[str, Any]:
    acts = safe_list(structure.get("acts"))
    intents: List[Dict[str, Any]] = []

    # Vega intro
    if safe_dict(director.get("vega_plan")).get("use_intro"):
        intents.append(vega_intro_intent())

    # Show open
    intents.append(show_open_intent(structure))

    # Acts
    for i, act in enumerate(acts):
        intents.append(act_intro_intent(act))

        stories = safe_list(act.get("stories"))

        for story in stories:
            roles = safe_dict(story.get("anchor_roles"))
            lead = clean(roles.get("lead"))
            counter = clean(roles.get("counter"))

            intents.append(question_intent(lead, story))

            if story.get("debate"):
                intents.append(challenge_intent(counter, story))

        # Transition
        if i < len(acts) - 1:
            next_domain = clean(acts[i + 1].get("domain"))
            intents.append(bridge_intent(next_domain))

    # Bitsy
    bitsy_plan = safe_dict(director.get("bitsy_plan"))
    if bitsy_plan.get("enabled"):
        intents.append(bitsy_toss_intent())

    # Close
    intents.append(show_close_intent())

    # Vega outro
    if safe_dict(director.get("vega_plan")).get("use_outro"):
        intents.append(vega_outro_intent())

    return {
        "generated_at": now_ts(),
        "chip_profile": CHIP_PROFILE,
        "intent_count": len(intents),
        "intents": intents
    }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    if not SHOW_STRUCTURE_PATH.exists():
        raise FileNotFoundError("Missing show_structure.json")

    if not SHOW_DIRECTOR_PATH.exists():
        raise FileNotFoundError("Missing show_director.json")

    show_structure = json.loads(SHOW_STRUCTURE_PATH.read_text())
    show_director = json.loads(SHOW_DIRECTOR_PATH.read_text())

    payload = build_host_intents(show_structure, show_director)

    atomic_write(OUTPUT_PATH, TMP_OUTPUT_PATH, payload)

    print(f"[HOST INTENTS] intents={payload['intent_count']}")

if __name__ == "__main__":
    main()
