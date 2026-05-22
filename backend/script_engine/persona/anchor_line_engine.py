#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS — ANCHOR LINE ENGINE v1.0

Purpose
-------
Transforms raw dialogue blocks into:
• personality-driven anchor lines
• multi-model generated dialogue
• OpenClaw agent-enhanced responses

This is the PRIMARY intelligence layer.

Author: TOKN Systems
"""

from __future__ import annotations

import json
import os
import subprocess
from typing import Dict, Any, List

from backend.script_engine.persona.anchor_router import route_anchor_panel
from backend.script_engine.character_brain.persona_loader import build_persona_prompt_context


# ---------------------------------------------------
# CONFIG
# ---------------------------------------------------

USE_OPENCLAW = os.getenv("TOKN_USE_OPENCLAW", "1") == "1"


# ---------------------------------------------------
# HELPERS
# ---------------------------------------------------

def clean(v):
    return "" if v is None else str(v).strip()


def safe_list(v):
    return v if isinstance(v, list) else []


# ---------------------------------------------------
# OPENCLAW EXECUTION
# ---------------------------------------------------

def run_openclaw(agent: str, message: str) -> str:
    try:
        result = subprocess.run(
            [
                "openclaw",
                "agent",
                "--agent", agent,
                "--message", message,
                "--local",
                "--json"
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            return message

        data = json.loads(result.stdout)

        # 🔥 CORRECT PARSING
        return (
            clean(data.get("result", {})
                      .get("message", {})
                      .get("content"))
            or message
        )

    except Exception:
        return message

# ---------------------------------------------------
# PROMPT BUILDER
# ---------------------------------------------------

def build_anchor_prompt(anchor_ctx: Dict[str, Any], base_text: str) -> str:

    persona_lines = anchor_ctx.get("persona_lines", [])
    phrasing = anchor_ctx.get("analysis_phrasing", [])
    structure = anchor_ctx.get("analysis_structure", [])

    return f"""
You are {anchor_ctx['display_name']} on Token News.

PERSONALITY:
{chr(10).join(persona_lines[:5])}

STYLE:
- Use phrases like: {', '.join(phrasing[:3])}
- Structure: {', '.join(structure[:2])}

TASK:
Rewrite this line in your voice with insight, not repetition:

"{base_text}"

RULES:
- Do NOT repeat the sentence
- Add insight or perspective
- Keep it concise
- Sound natural for broadcast

Return ONLY the rewritten line.
"""


# ---------------------------------------------------
# MAIN ENGINE
# ---------------------------------------------------

def generate_segment_lines(block: Dict[str, Any]) -> List[Dict[str, str]]:

    routing = route_anchor_panel(block)

    turns = safe_list(block.get("dialogue"))

    output_turns = []

    for i, turn in enumerate(turns):

        base_text = clean(turn.get("text"))
        if not base_text:
            continue

        # rotate anchors
        anchor = routing["panel"][i % len(routing["panel"])]
        anchor_id = anchor["anchor_id"]

        persona_ctx = build_persona_prompt_context(anchor_id)

        prompt = build_anchor_prompt(persona_ctx, base_text)

        # -----------------------------
        # MODEL ROUTING
        # -----------------------------
        if USE_OPENCLAW:
            line = run_openclaw(anchor_id, prompt)
        else:
            line = base_text

        output_turns.append({
            "speaker": anchor_id,
            "text": line
        })

    return output_turns


# ---------------------------------------------------
# BATCH
# ---------------------------------------------------

def generate_all(dialogue_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    out = []

    for block in dialogue_blocks:

        new_block = dict(block)

        new_block["dialogue"] = generate_segment_lines(block)

        out.append(new_block)

    return out


# ---------------------------------------------------
# ENTRY
# ---------------------------------------------------

if __name__ == "__main__":

    INPUT = "/opt/toknnews/data/stories/dialogue_blocks.json"
    OUTPUT = "/opt/toknnews/data/stories/dialogue_blocks_enriched.json"

    data = json.loads(open(INPUT).read())

    enriched = generate_all(data)

    with open(OUTPUT, "w") as f:
        json.dump(enriched, f, indent=2)

    print(f"[LINE ENGINE] Generated {len(enriched)} enriched blocks")
