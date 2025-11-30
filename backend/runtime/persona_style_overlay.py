#!/usr/bin/env python3
"""
persona_style_overlay.py
TOKEN NEWS — Dynamic Persona Style Overlay Engine

This module dynamically modifies GPT persona output based on:
 - daypart (morning/afternoon/evening/latenight)
 - show_mode (NEWS/LATENIGHT/BREAKING)
 - PD flags (volatility, social heat, breaking)
 - persona mood (continuously updated)
 - conversational memory context
 - runtime pacing / urgency
"""

import random


# ======================================================================
# STYLE RULES
# ======================================================================

DAYPART_TONES = {
    "morning": (
        "Slightly calmer tone. Focus on clarity. "
        "Welcoming energy but not overly excited."
    ),
    "afternoon": (
        "Neutral newsroom tone. Balanced pacing. "
        "Confident but not dramatic."
    ),
    "evening": (
        "More narrative weight. Slightly deeper tone. "
        "Reflective and composed."
    ),
    "latenight": (
        "Looser, more expressive tone. Slightly witty or clever. "
        "More personality allowed, except in tragic contexts."
    )
}

SHOWMODE_TONE = {
    "NEWS": "Maintain professional tone. No humor unless persona allows it.",
    "LATENIGHT": (
        "Energy can be higher. Sarcasm and wit permitted for personas who support it. "
        "Avoid disrespecting serious or tragic stories."
    ),
    "BREAKING": (
        "Sharper tone. Focus on facts. Avoid humor entirely. "
        "Brief, urgent delivery. Stay calm but efficient."
    )
}


PD_FLAG_EFFECTS = {
    "volatility_high": (
        "Acknowledge elevated uncertainty; speak with caution or urgency "
        "depending on persona role."
    ),
    "social_heat_high": (
        "Use culturally aware tone. Avoid inflammatory phrasing. "
        "Be sensitive to crowd reactions."
    ),
    "breaking_true": (
        "High alert mode. Stay concise and serious. "
        "Avoid embellishment of any kind."
    )
}


# ======================================================================
# MOOD LAYERS (Persona Drift)
# ======================================================================

MOOD_TONES = {
    "calm": "Keep responses steady and measured.",
    "confident": "Add assertiveness and clarity.",
    "excited": "Increase energy and pace slightly.",
    "tired": "Slightly slower and more reflective.",
    "stressed": "Sharper focus; shorter phrasing.",
    "playful": "Allow small stylistic quirks or wit (if persona fits).",
    "chaotic": "Break rules slightly; unpredictable vibe (Bitsy, Rex only)."
}


# ======================================================================
# MEMORY-RESPONSIVE OVERLAYS
# ======================================================================

def memory_overlay(memory):
    """
    Produce a memory-related style injection from:
      memory = {
         "recent": [...],
         "episode": {...},
         "long_term": [...]
      }
    """
    overlays = []

    # Recent line references
    if memory["recent"]:
        last = memory["recent"][0]
        overlays.append(
            f"Reference earlier when {last['speaker']} said: \"{last['text']}\" "
            "if contextually appropriate."
        )

    # Episode theme
    if "theme" in memory["episode"]:
        overlays.append(
            f"Episode theme detected: {memory['episode']['theme']}. "
            "Keep your phrasing aligned with this tone."
        )

    # Running long-term jokes/threads
    for item in memory["long_term"]:
        content = item["content"]
        strength = item["strength"]

        # Only include strong memories
        if strength > 0.3:
            overlays.append(
                f"You may subtly reference this past detail: '{content}'."
            )

    return overlays


# ======================================================================
# MAIN OVERLAY BUILDER
# ======================================================================

def build_style_overlay(
    persona: str,
    daypart: str,
    show_mode: str,
    pd_flags: dict,
    mood: str,
    memory_context: dict
) -> str:
    """
    Returns a long string injected into GPT prompts that modifies output style.
    """

    tone_layers = []

    # Daypart adjustment
    tone_layers.append(DAYPART_TONES.get(daypart, ""))

    # Show mode adjustment
    tone_layers.append(SHOWMODE_TONE.get(show_mode, ""))

    # PD flags
    if pd_flags.get("is_breaking"):
        tone_layers.append(PD_FLAG_EFFECTS["breaking_true"])

    if pd_flags.get("volatility_risk", 0) > 0.5:
        tone_layers.append(PD_FLAG_EFFECTS["volatility_high"])

    if pd_flags.get("social_heat", 0) > 0.5:
        tone_layers.append(PD_FLAG_EFFECTS["social_heat_high"])

    # Persona mood
    tone_layers.append(MOOD_TONES.get(mood, ""))

    # Memory-aware overlays
    tone_layers.extend(memory_overlay(memory_context))

    # Final concatenation
    overlay_string = "\n".join([t for t in tone_layers if t])

    return overlay_string.strip()


# ======================================================================
# TEST
# ======================================================================
if __name__ == "__main__":
    test_memory = {
        "recent": [{"speaker": "chip", "text": "Let's zoom out for a moment."}],
        "episode": {"theme": "market stress"},
        "long_term": [{"type": "joke", "content": "Reef always mocks bridge risk", "strength": 0.9}]
    }

    out = build_style_overlay(
        persona="reef",
        daypart="evening",
        show_mode="NEWS",
        pd_flags={"is_breaking": False, "volatility_risk": 0.7, "social_heat": 0.2},
        mood="confident",
        memory_context=test_memory
    )

    print(out)
