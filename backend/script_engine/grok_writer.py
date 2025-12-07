#!/usr/bin/env python3
"""
grok_writer.py
ToknNews 2025 — Canonical Conversation Engine with Batching (Transfer Brain v1.0)

Two GPT modes:
 - write_block_conversation()  → single-story (Breaking Mode)
 - write_batch_conversations() → multi-story batch (default timeline pipeline)
"""

from __future__ import annotations
from typing import Optional, List, Dict, Any

from openai import OpenAI
from backend.runtime.vault_loader import load_secrets
from script_engine.character_brain.persona_loader import get_persona_lines


# ---------------------------------------------------------------
# OpenAI Client
# ---------------------------------------------------------------

_secrets = load_secrets()
OPENAI_API_KEY = _secrets.get("openai_api_key", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ---------------------------------------------------------------
# Persona utilities
# ---------------------------------------------------------------

def _persona_profile(name: str) -> str:
    try:
        lines = get_persona_lines(name)
    except Exception:
        lines = []
    summary = " ".join(lines).strip() or f"{name.capitalize()} is an anchor on ToknNews."
    summary = " ".join(summary.split())
    return f"{name.capitalize()} is an anchor on ToknNews. {summary}"


# ---------------------------------------------------------------
# Clean GPT output
# ---------------------------------------------------------------

def _clean(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`").strip()
    return t


# ---------------------------------------------------------------
# SINGLE-STORY CONVERSATION (Preserved for Breaking Mode)
# ---------------------------------------------------------------

def write_block_conversation(
    primary: str,
    headline: str,
    synthesis: str,
    scene_state: Optional[dict] = None,
    episode_id: str = "",
    secondary: Optional[str] = None,
) -> str:

    primary = primary.lower()
    secondary = secondary.lower() if secondary else None

    anchors: List[str] = []
    if primary != "chip":
        anchors.append(primary)
    if secondary and secondary not in anchors and secondary != "chip":
        anchors.append(secondary)

    if not anchors:
        return f"Chip: {synthesis or headline}\n{primary.capitalize()}: That's the key takeaway."

    chip_profile = _persona_profile("chip")
    profiles = {name: _persona_profile(name) for name in anchors}

    prompt = f"""
Generate a ToknNews conversation for ONE story.

[STORY 1]
Headline: {headline}
Summary: {synthesis}

Characters:
- {chip_profile}
"""
    for name, desc in profiles.items():
        prompt += f"- {desc}\n"

    prompt += f"""
Rules:
- Chip opens by prompting {anchors[0].capitalize()}.
- 4–6 total lines.
- No greetings, no narrator text, no hype.
- Do NOT repeat the headline verbatim.
- Format:
  Chip: ...
  {anchors[0].capitalize()}: ...
"""

    if client:
        try:
            rsp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.5,
                timeout=12
            )
            return _clean(rsp.choices[0].message.content)
        except Exception:
            pass

    # Fallback
    lines = [
        f"Chip: {synthesis or headline} — what's your take?",
        f"{anchors[0].capitalize()}: It's meaningful, but the market context matters more.",
    ]
    if len(anchors) > 1:
        lines.append(
            f"{anchors[1].capitalize()}: Agreed, but the narrative is shifting faster than traders expect."
        )
    return "\n".join(lines)


# ---------------------------------------------------------------
# BATCHED MULTI-STORY CONVERSATION (5 at a time)
# ---------------------------------------------------------------

def write_batch_conversations(batch: List[Dict[str, Any]]):
    """
    batch = [
      {
        "headline": "...",
        "summary": "...",
        "primary": "cash",
        "secondary": "bond"
      },
      ...
    ]

    Returns list[str] where each string is a multi-line conversation.
    """

    if not batch:
        return []

    # Build persona profiles involved in this batch
    persona_map = {}

    for item in batch:
        primary = item["primary"]
        secondary = item.get("secondary")
        persona_map[primary] = _persona_profile(primary)
        if secondary:
            persona_map[secondary] = _persona_profile(secondary)

    persona_map["chip"] = _persona_profile("chip")

    # Construct GPT prompt
    prompt = "Generate ToknNews conversations for multiple stories.\n\n"
    prompt += "Format exactly like this:\n"
    prompt += "[STORY 1]\nChip: ...\n<anchor>: ...\n\n"
    prompt += "[STORY 2]\nChip: ...\n<anchor>: ...\n\n"
    prompt += "No extra commentary.\n\n"

    # Add character descriptions
    prompt += "Characters:\n"
    for name, desc in persona_map.items():
        prompt += f"- {desc}\n"

    # Add stories
    for idx, item in enumerate(batch, start=1):
        prompt += f"""
[STORY {idx}]
Headline: {item['headline']}
Summary: {item['summary']}
Primary: {item['primary']}
Secondary: {item.get('secondary') or 'None'}

""".strip() + "\n"

    # GPT CALL
    if client:
        try:
            rsp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=900,
                temperature=0.5,
                timeout=15
            )
            raw = _clean(rsp.choices[0].message.content)
        except Exception:
            raw = ""
    else:
        raw = ""

    # If GPT failed, fallback for each story
    if not raw:
        results = []
        for item in batch:
            p = item["primary"]
            s = item.get("secondary")
            lines = [
                f"Chip: {item['summary']} — what's your take?",
                f"{p.capitalize()}: The implications are bigger than traders think.",
            ]
            if s:
                lines.append(
                    f"{s.capitalize()}: And people watching charts alone are going to miss it."
                )
            results.append("\n".join(lines))
        return results

    # Parse GPT sectioned output
    outputs = raw.split("[STORY ")
    conversations = []

    for block in outputs:
        block = block.strip()
        if not block or not block[0].isdigit():
            continue
        # remove leading id
        block = block.split("]", 1)[1].strip()
        conversations.append(block)

    # Guarantee correct count
    if len(conversations) != len(batch):
        while len(conversations) < len(batch):
            # fallback fillers
            item = batch[len(conversations)]
            p = item["primary"]
            s = item.get("secondary")
            lines = [
                f"Chip: {item['summary']} — what's your take?",
                f"{p.capitalize()}: The implications are bigger than traders think."
            ]
            if s:
                lines.append(
                    f"{s.capitalize()}: And people watching charts alone are going to miss it."
                )
            conversations.append("\n".join(lines))

    return conversations


if __name__ == "__main__":
    print("[GW] batched grok_writer loaded successfully.")
