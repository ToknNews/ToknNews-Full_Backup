#!/usr/bin/env python3
"""
grok_writer_v5.py
ToknNews 2025 — Conversational Engine v5
True multi-anchor conversational dynamics + LateNight mode.

Inputs (from PD Engine v4.5):
[
  {
    "story": {... enriched story ...},
    "primary": "cash",
    "secondary": "bond",
    "tertiary": "ivy" or None,
    "anchors": ["cash","bond","ivy"],
    "heat": int,
    "domain": "markets"
  },
  ...
]

Outputs:
A list of raw conversation strings, one per story.
Each string is parsed by Timeline Builder → blocks → TTS.

"""

from __future__ import annotations
from typing import List, Dict, Any
from openai import OpenAI

from backend.runtime.vault_loader import load_secrets
from script_engine.character_brain.persona_loader import get_persona_lines


# -----------------------------------------------------------
# OpenAI setup
# -----------------------------------------------------------

_secrets = load_secrets()
OPENAI_API_KEY = _secrets.get("openai_api_key", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# -----------------------------------------------------------
# Persona Loading
# -----------------------------------------------------------

def _persona_profile(name: str) -> str:
    """
    Returns longform persona description.
    If persona_loader has deep rules, we use them fully.
    """
    try:
        lines = get_persona_lines(name) or []
    except Exception:
        lines = []

    summary = " ".join(lines).strip()
    if not summary:
        summary = f"{name.capitalize()} is an anchor on ToknNews."

    summary = " ".join(summary.split())
    return summary


# -----------------------------------------------------------
# Clean GPT output
# -----------------------------------------------------------

def _clean(t: str) -> str:
    if not t:
        return ""
    t = t.strip()
    if t.startswith("```"):
        t = t.strip("`").strip()
    return t


# -----------------------------------------------------------
# Build conversation prompt (core intelligence)
# -----------------------------------------------------------

def _build_prompt(batch: List[Dict[str,Any]], latenight: bool) -> str:

    prompt = "Generate realistic ToknNews anchor conversations.\n\n"

    if latenight:
        prompt += "LateNight Mode ON → anchors may be slightly looser, witty, dry, or sarcastic.\n"
        prompt += "Still professional, but more human.\n\n"

    prompt += "Rules:\n"
    prompt += "- Chip leads transitions.\n"
    prompt += "- Anchors respond to *each other*, not just the summary.\n"
    prompt += "- They may disagree, challenge, acknowledge, or build on points.\n"
    prompt += "- NO headline repetition.\n"
    prompt += "- 4–7 lines per story.\n"
    prompt += "- Format ONLY as:\n"
    prompt += "  Chip: ...\n"
    prompt += "  Cash: ...\n"
    prompt += "  Bond: ...\n"
    prompt += "\nNo narration, no explanations.\n\n"

    # Persona descriptions
    prompt += "Character Profiles:\n"
    personas = set()
    for item in batch:
        personas.add("chip")
        personas.update(item["anchors"])

    for p in personas:
        prompt += f"- {p.capitalize()}: {_persona_profile(p)}\n"

    # Add story payloads
    for i, item in enumerate(batch, start=1):
        s = item["story"]
        summary = s.get("summary") or ""
        summary = summary.replace("\n"," ").strip()

        prompt += f"\n[STORY {i}]\n"
        prompt += f"Summary: {summary}\n"
        prompt += f"Primary: {item['primary']}\n"
        prompt += f"Secondary: {item.get('secondary') or 'None'}\n"
        prompt += f"Domain: {item['domain']}\n"
        prompt += f"Heat: {item['heat']}\n"

        if item.get("tertiary"):
            prompt += f"Tertiary: {item['tertiary']}\n"

    return prompt


# -----------------------------------------------------------
# Parse GPT output back into per-story sections
# -----------------------------------------------------------

def _split_conversations(raw: str, count: int) -> List[str]:
    out = []
    blocks = raw.split("[STORY ")

    for b in blocks:
        b = b.strip()
        if not b or not b[0].isdigit():
            continue
        conv = b.split("]",1)[1].strip()
        out.append(conv)

    # Ensure count matches required
    while len(out) < count:
        out.append("Chip: Let's unpack this.\n")

    return out[:count]


# -----------------------------------------------------------
# PUBLIC API: produce conversations for multiple stories
# -----------------------------------------------------------

def write_batch_conversations_v5(batch: List[Dict[str,Any]], latenight=False) -> List[str]:

    if not batch:
        return []

    prompt = _build_prompt(batch, latenight)

    if client:
        try:
            rsp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1500,
                temperature=0.55 if not latenight else 0.75,
                timeout=18
            )
            raw = _clean(rsp.choices[0].message.content)
        except Exception as e:
            print("[GWv5] GPT ERROR:", e)
            raw = ""
    else:
        raw = ""

    # If GPT failed → fallback
    if not raw:
        fallbacks = []
        for item in batch:
            s = item["story"]["summary"]
            p = item["primary"].capitalize()
            fallback = f"Chip: {s} — what's your read?\n{p}: It's meaningful context.\n"
            fallbacks.append(fallback)
        return fallbacks

    # Split into individual conversation blocks
    conversations = _split_conversations(raw, len(batch))
    return conversations


if __name__ == "__main__":
    print("grok_writer_v5 loaded successfully.")
