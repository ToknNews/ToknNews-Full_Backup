#!/usr/bin/env python3
"""
grok_writer.py
TOKEN NEWS — Character Conversation Engine (OpenAI)

Generates multi-line dialogue blocks between Chip and one or more anchor
characters for ToknNews.

This replaces the old per-line writer. It is intentionally small:
 - takes a headline + synthesis
 - uses persona_loader to pull longform persona text
 - asks OpenAI for a short back-and-forth conversation
"""

from __future__ import annotations

from typing import Optional, Dict, List

from openai import OpenAI

from backend.runtime.vault_loader import load_secrets
from script_engine.character_brain.persona_loader import get_persona_lines

# --------------------------------------------------------------------
# OpenAI client
# --------------------------------------------------------------------
_secrets = load_secrets()
OPENAI_API_KEY = _secrets.get("openai_api_key", "")

if OPENAI_API_KEY:
    client = OpenAI(api_key=OPENAI_API_KEY)
else:
    client = None
    print("[GrokWriter] WARNING: OPENAI_API_KEY is empty; using fallback dialogue only.")

# --------------------------------------------------------------------
# Persona helpers
# --------------------------------------------------------------------
def _persona_profile(name: str) -> str:
    """
    Build a third‑person description of the anchor from character_brain.json
    via persona_loader.get_persona_lines().
    """
    try:
        lines = get_persona_lines(name)
    except Exception:
        lines = []

    name_cap = name.capitalize()
    if not lines:
        return f"{name_cap} is an anchor on Token News with a distinct on‑air style."

    summary = " ".join(lines)
    summary = " ".join(summary.split())  # collapse whitespace
    return f"{name_cap} is an anchor on Token News. {summary}"


def _clean_model_output(text: str) -> str:
    """
    Strip fences / wrapping quotes so timeline_builder can split on newlines.
    """
    if not text:
        return ""

    t = text.strip()

    # remove simple code fences
    if t.startswith("```"):
        t = t.strip("`").strip()

    # trim surrounding quotes
    if t.startswith('"') and t.endswith('"'):
        t = t[1:-1].strip()

    return t


# --------------------------------------------------------------------
# Public API
# --------------------------------------------------------------------
def write_block_conversation(
    primary: str,
    headline: str,
    synthesis: str = "",
    scene_state: Optional[dict] = None,
    episode_id: str = "",
    secondary: Optional[str] = None,
) -> str:
    """
    Generate a full multi-line dialogue between Chip and other anchor(s).

    Returns a string where each line looks like:
        Chip: ...
        Ivy:  ...
        Cash: ...
    """
    print(f"[GW DEBUG] primary={primary}, secondary={secondary}, headline={headline}")

    primary = (primary or "chip").lower()
    secondary = secondary.lower() if secondary else None

    # anchors other than Chip that will appear in the block
    others: List[str] = []
    if primary != "chip":
        others.append(primary)
    if secondary and secondary not in others and secondary != "chip":
        others.append(secondary)

    # If nothing but Chip is left, just make a simple two-line exchange.
    if not others:
        synth = synthesis if synthesis else ""
        return f"Chip: {headline}?\n{primary.capitalize()}: {synth}"

    chip_profile = _persona_profile("chip")
    profiles: Dict[str, str] = {name: _persona_profile(name) for name in others}

    other_display = " and ".join(n.capitalize() for n in others)

    characters_section = "Characters:\n"
    characters_section += f"- {chip_profile}\n"
    for name in others:
        characters_section += f"- {profiles[name]}\n"

    prompt = f"""
The following is a live conversation on Token News about a crypto / markets story.

Headline: {headline}
Summary: {synthesis or 'N/A'}

{characters_section}
Instructions:
- Chip (the host) opens by prompting {others[0].capitalize()} about the story.
- Chip stays calm and precise, keeping the conversation moving.
- {other_display} {'are' if len(others) > 1 else 'is'} more impulsive or colorful in commentary.
- Brief banter is fine, but keep it tight and information-dense.
- Do NOT repeat the headline verbatim. Talk about implications, risk and context.
- No greetings, no sign-offs, no narrator text.
- Aim for roughly 4–6 lines of dialogue total.
- Format output as plain lines like:
  Chip: ...
  Ivy: ...
  Cash: ...
- Do not include any explanations before or after the dialogue.
""".strip()

    # If we don't have a configured client, fall back to a deterministic script.
    if client is None:
        print("[GrokWriter] Using deterministic fallback conversation (no OpenAI client).")
        lines = [
            f"Chip: {headline} — what are we really looking at here?",
            f"{others[0].capitalize()}: {synthesis or 'It moves the risk needle more than the price action shows.'}",
        ]
        if len(others) > 1:
            lines.append(
                f"{others[1].capitalize()}: And as usual, the market is late to that party."
            )
        return "\n".join(lines)

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=220,
            temperature=0.8,
        )
        raw = response.choices[0].message.content or ""
        return _clean_model_output(raw)
    except Exception as e:  # pragma: no cover - defensive path
        print("[GrokWriter] ERROR generating conversation:", e)
        # Structured but simple fallback
        fallback_lines = [
            f"Chip: {headline} — give it to us straight.",
            f"{others[0].capitalize()}: {synthesis or 'Short version: risk is shifting faster than the headline suggests.'}",
        ]
        if len(others) > 1:
            fallback_lines.append(
                f"{others[1].capitalize()}: Perfect setup for people who only skim the chart."
            )
        return "\n".join(fallback_lines)
