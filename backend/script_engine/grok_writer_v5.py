#!/usr/bin/env python3
"""
grok_writer_v6.py
ToknNews — Broadcast Brain v6

Upgrades:
- Explicit continuity (last N episodes)
- Anchor-aware memory
- Narrative phase awareness
- Mode-sensitive tone (NEWS vs CHAOS/LATE_NIGHT)
- Clean output for TimelineBuilder v5+
"""

from __future__ import annotations
from typing import List, Dict, Any
import json
import os
from openai import OpenAI

from backend.runtime.vault_loader import load_secrets
from script_engine.character_brain.persona_loader import get_persona_lines


# -----------------------------------------------------------
# CONFIG
# -----------------------------------------------------------

MODEL_DEFAULT = "gpt-4.1"
MEMORY_EPISODES = 5
EPISODE_DIR = "/opt/toknnews/data/episodes"


# -----------------------------------------------------------
# OpenAI setup
# -----------------------------------------------------------

_secrets = load_secrets()
OPENAI_API_KEY = _secrets.get("openai_api_key", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# -----------------------------------------------------------
# MEMORY LOADERS
# -----------------------------------------------------------

def _load_recent_episode_memory(limit=MEMORY_EPISODES) -> List[Dict[str,Any]]:
    if not os.path.exists(EPISODE_DIR):
        return []

    metas = []
    for f in os.listdir(EPISODE_DIR):
        if f.endswith("_meta.json"):
            try:
                meta = json.load(open(os.path.join(EPISODE_DIR, f)))
                metas.append(meta)
            except Exception:
                pass

    metas = sorted(metas, key=lambda x: x.get("timestamp", 0), reverse=True)
    return metas[:limit]


def _summarize_memory(memory: List[Dict[str,Any]]) -> str:
    if not memory:
        return "No recent episode context."

    lines = []
    for m in memory:
        lines.append(
            f"- {m.get('mode','NEWS')} episode recently covered "
            f"{m.get('used_story_count','multiple')} stories."
        )

    return "\n".join(lines)


# -----------------------------------------------------------
# PERSONA
# -----------------------------------------------------------

def _persona_profile(name: str) -> str:
    try:
        lines = get_persona_lines(name) or []
    except Exception:
        lines = []

    summary = " ".join(lines).strip()
    if not summary:
        summary = f"{name.capitalize()} is a ToknNews anchor."

    return summary


# -----------------------------------------------------------
# PROMPT BUILDER
# -----------------------------------------------------------

def _build_prompt(
    story: Dict[str,Any],
    primary: str,
    secondary: str | None,
    tertiary: str | None,
    mode: str,
    memory_summary: str,
) -> str:

    latenight = mode in ("CHAOS", "LATE_NIGHT")

    tone = (
        "LateNight Mode → sharper, looser, dry humor allowed.\n"
        if latenight else
        "Broadcast Mode → professional, measured, confident.\n"
    )

    anchors = [a for a in [primary, secondary, tertiary] if a]

    prompt = f"""
You are writing a REAL ToknNews broadcast conversation.

{tone}

GLOBAL RULES:
- Chip leads transitions.
- Anchors must acknowledge or respond to each other.
- Use explicit callbacks when relevant (\"Yesterday we said…\", \"Earlier this week…\").
- No headline repetition.
- 4–7 total lines.
- Natural broadcast pacing.

RECENT CONTEXT:
{memory_summary}

CHARACTER PROFILES:
"""
    prompt += "\n".join(
        f"- {a.capitalize()}: {_persona_profile(a)}"
        for a in ["chip"] + anchors
    )

    summary = story.get("summary","").replace("\n"," ").strip()
    phase = story.get("phase","escalation")

    prompt += f"""

STORY:
Summary: {summary}
Domain: {story.get("domain")}
Heat: {story.get("importance", 5)}
Narrative Phase: {phase}

FORMAT EXACTLY AS:
Chip: ...
Anchor: ...
"""

    return prompt.strip()


# -----------------------------------------------------------
# GPT CALL
# -----------------------------------------------------------

def _call_gpt(prompt: str, latenight: bool) -> str:
    if not client:
        return ""

    try:
        rsp = client.chat.completions.create(
            model=MODEL_DEFAULT,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.55 if not latenight else 0.75,
            max_tokens=700,
            timeout=20
        )
        return rsp.choices[0].message.content.strip()
    except Exception as e:
        print("[GWv6] GPT ERROR:", e)
        return ""


# -----------------------------------------------------------
# PUBLIC API (TimelineBuilder compatible)
# -----------------------------------------------------------

def generate_conversation(
    story: Dict[str,Any],
    primary: str,
    secondary: str | None = None,
    tertiary: str | None = None,
    mode: str = "NEWS",
) -> List[Dict[str,str]]:

    memory = _load_recent_episode_memory()
    memory_summary = _summarize_memory(memory)

    prompt = _build_prompt(
        story=story,
        primary=primary,
        secondary=secondary,
        tertiary=tertiary,
        mode=mode,
        memory_summary=memory_summary,
    )

    raw = _call_gpt(prompt, latenight=(mode in ("CHAOS","LATE_NIGHT")))

    # Fallback
    if not raw:
        return [
            {"speaker":"chip","text":"Let’s zoom out for a second.","tag":"chip_transition"},
            {"speaker":primary,"text":"This one matters more than it looks.","tag":"anchor_analysis"}
        ]

    lines = []
    for ln in raw.splitlines():
        if ":" not in ln:
            continue
        sp, txt = ln.split(":",1)
        speaker = sp.strip().lower()
        text = txt.strip()

        tag = "chip_transition" if speaker == "chip" else "anchor_analysis"

        lines.append({
            "speaker": speaker,
            "text": text,
            "tag": tag,
        })

    return lines


if __name__ == "__main__":
    print("GrokWriter v6 loaded.")
