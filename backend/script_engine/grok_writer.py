#!/usr/bin/env python3
"""
grok_writer_v4.py
ToknNews 2025 — Deep Editorial Conversation Engine

This engine generates *fully contextual*, *persona-aware*,
*interpersonal* newsroom conversations.

It consumes enriched stories from the Editorial Engine v4:

{
    "headline": "...",
    "summary": "...",
    "domain": "...",
    "signals": {
        "price_trend": ...,
        "volume_spike": ...,
        "whale_activity": ...,
        "gas_pressure": ...,
        "liquidity_pressure": ...,
        "composite_heat": 0-10,
    }
}

Conversation Rules v4:
- Chip frames the story using summary + signals
- Primary anchor responds with context or challenge
- Secondary anchor provides disagreement OR deeper insight
- Anchors may address each other by name
- Bitsy meta-interrupt (probability controlled by Timeline Builder)
- Vega color-lines ONLY via Timeline Builder, never here
- LateNight persona shift supported via `latenight` flag
"""

from __future__ import annotations
from typing import List, Dict, Any, Optional
import random

from openai import OpenAI
from backend.runtime.vault_loader import load_secrets
from script_engine.character_brain.persona_loader import get_persona_lines


# ============================================================
# OPENAI CLIENT
# ============================================================

_secrets = load_secrets()
OPENAI_API_KEY = _secrets.get("openai_api_key", "")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# ============================================================
# Persona Profiles
# ============================================================

def _persona_profile(name: str) -> str:
    """
    Loads persona description from character_brain.json
    """
    try:
        lines = get_persona_lines(name)
        summary = " ".join(lines).strip()
        summary = " ".join(summary.split())
        return f"{name.capitalize()} is an anchor on ToknNews. {summary}"
    except Exception:
        return f"{name.capitalize()} is an anchor on ToknNews."


# ============================================================
# GPT CLEANER
# ============================================================

def _clean(text: str) -> str:
    if not text:
        return ""
    t = text.strip()
    if t.startswith("```"):
        t = t.strip("`").strip()
    return t


# ============================================================
# BUILD SIGNAL PHRASES
# ============================================================

def _signal_context(signals: Dict[str, Any]) -> str:
    """
    Convert quantitative signals into clean editorial cues for GPT.
    """
    if not signals:
        return ""

    cues = []

    pt = signals.get("price_trend")
    if pt == "up":
        cues.append("price momentum is rising")
    if pt == "down":
        cues.append("price is showing downward pressure")

    if signals.get("volume_spike"):
        cues.append("volume is spiking unusually high")

    if signals.get("whale_activity"):
        cues.append("whale flows were detected")

    if signals.get("gas_pressure"):
        cues.append("network congestion is rising")

    if signals.get("liquidity_pressure"):
        cues.append("liquidity conditions look thin")

    heat = signals.get("composite_heat", 0)
    if heat >= 6:
        cues.append(f"overall risk heat is elevated ({heat}/10)")
    elif heat >= 3:
        cues.append(f"risk heat is moderate ({heat}/10)")

    return "; ".join(cues)


# ============================================================
# SINGLE-STORY CONVERSATION (Breaking Mode)
# ============================================================

def write_block_conversation(story: Dict[str, Any],
                             primary: str,
                             secondary: Optional[str],
                             latenight: bool = False) -> str:

    primary = primary.lower()
    secondary = secondary.lower() if secondary else None

    signals = story.get("signals", {})
    signal_text = _signal_context(signals)
    summary = story.get("summary", "")
    headline = story.get("headline", "")

    chip_profile = _persona_profile("chip")
    p1_profile = _persona_profile(primary)
    p2_profile = _persona_profile(secondary) if secondary else ""

    # Build prompt
    prompt = f"""
Generate a ToknNews conversation for ONE story.

Headline: {headline}
Summary: {summary}
Signals: {signal_text or "none"}

Mode: {"LateNight" if latenight else "Standard"}

Characters:
- {chip_profile}
- {p1_profile}
"""
    if secondary:
        prompt += f"- {p2_profile}\n"

    prompt += """
Conversation Rules:
- 4–7 total lines.
- Chip opens with a *contextual framing* using summary + signals.
- Primary anchor responds directly to Chip.
- Secondary anchor adds disagreement OR supporting detail.
- Anchors may address each other by name.
- No greetings, no hype, no jokes unless LateNight is ON.
- Do NOT repeat headline verbatim.
Format ONLY as:
Chip: ...
<Anchor>: ...
<Anchor>: ...
"""

    # GPT CALL
    if client:
        try:
            rsp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=260,
                temperature=0.55 if not latenight else 0.8,
                timeout=12
            )
            return _clean(rsp.choices[0].message.content)
        except Exception:
            pass

    # Fallback
    base = f"Chip: {summary} — {signal_text if signal_text else ''} What's your read, {primary.capitalize()}?"
    p1 = f"{primary.capitalize()}: The signal mix is meaningful — but the market context matters here."
    if secondary:
        p2 = f"{secondary.capitalize()}: I see it differently — the underlying flows tell another story."
        return "\n".join([base, p1, p2])
    return "\n".join([base, p1])


# ============================================================
# MULTI-STORY BATCH CONVERSATION (Timeline Engine)
# ============================================================

def write_batch_conversations(batch: List[Dict[str, Any]],
                              latenight: bool = False) -> List[str]:

    if not batch:
        return []

    persona_map = {"chip": _persona_profile("chip")}
    for item in batch:
        persona_map[item["primary"]] = _persona_profile(item["primary"])
        if item.get("secondary"):
            persona_map[item["secondary"]] = _persona_profile(item["secondary"])

    # Prompt header
    prompt = "Generate ToknNews conversations for multiple stories.\n\n"
    prompt += "Format EXACTLY like:\n[STORY 1]\nChip: ...\n<Anchor>: ...\n\n"

    prompt += "\nCharacters:\n"
    for name, desc in persona_map.items():
        prompt += f"- {desc}\n"

    # Story slots
    for idx, item in enumerate(batch, start=1):
        s = item["story"]
        prompt += f"""
[STORY {idx}]
Headline: {s['headline']}
Summary: {s['summary']}
Signals: {_signal_context(s.get('signals', {}))}
Primary: {item['primary']}
Secondary: {item.get('secondary') or 'None'}
""".strip() + "\n"

    prompt += f"\nTone: {'LateNight — relaxed, sharper, more candid' if latenight else 'Standard newsroom tone'}\n"
    prompt += """
Rules:
- Chip opens every conversation.
- Anchors must refer to each other naturally (e.g. "Ivy’s right", "Bond, hold on—")
- 4–6 lines per story.
- No narrator text.
- Do NOT repeat headlines.
"""

    # GPT CALL
    if client:
        try:
            rsp = client.chat.completions.create(
                model="gpt-4o",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1600,
                temperature=0.55 if not latenight else 0.85,
                timeout=20
            )
            raw = _clean(rsp.choices[0].message.content)
        except Exception:
            raw = ""
    else:
        raw = ""

    # Parse GPT output
    if raw:
        sections = raw.split("[STORY ")
        out = []
        for sec in sections:
            sec = sec.strip()
            if not sec or not sec[0].isdigit():
                continue
            conv = sec.split("]", 1)[1].strip()
            out.append(conv)

        # Ensure count matches
        while len(out) < len(batch):
            item = batch[len(out)]
            out.append(
                f"Chip: {item['story']['summary']} — what's your take?\n"
                f"{item['primary'].capitalize()}: Context matters.\n"
            )

        return out

    # Fallback for GPT errors
    fallback = []
    for item in batch:
        fallback.append(
            f"Chip: {item['story']['summary']} — what's your take?\n"
            f"{item['primary'].capitalize()}: The implications are bigger than traders think."
        )
    return fallback


if __name__ == "__main__":
    print("[GWv4] Conversation engine loaded.")
