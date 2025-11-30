#!/usr/bin/env python3
"""
TOKNNews Character Brain Engine (v1 Scaffold)

This module provides:
 - Loading of personality DNA (character_brain.json)
 - Access to memory (future expansion)
 - Tone / bias / relationship hooks (future expansion)
 - A single entrypoint for the Script Engine:
       generate_persona_line(character, enriched)
"""

import json
import os
from script_engine.hybrid_tone.chip_tone_shaper import (
    compute_chip_tone_weight,
    apply_chip_tone_to_line,
)

BASE_DIR = os.path.dirname(__file__)

BRAIN_PATH = os.path.join(BASE_DIR, "character_brain.json")
MEMORY_PATH = os.path.join(BASE_DIR, "character_memory.json")


# ---------------------------------------------------------
# Load character brain (DNA)
# ---------------------------------------------------------
def load_brain():
    try:
        with open(BRAIN_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


# ---------------------------------------------------------
# Load persistent memory (future adaptive behavior)
# ---------------------------------------------------------
def load_memory():
    if not os.path.exists(MEMORY_PATH):
        return {}
    try:
        with open(MEMORY_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


def save_memory(memory):
    try:
        with open(MEMORY_PATH, "w") as f:
            json.dump(memory, f, indent=2)
    except Exception:
        pass


# ---------------------------------------------------------
# Persona line generator (placeholder)
# Script Engine v3 will call this function to generate
# character-aware lines based on the enriched payload.
# ---------------------------------------------------------
def generate_persona_line(character, enriched):
    brain = load_brain()
    mem = load_memory()
    profile = brain.get(character, {})

    # --- Vega Watt never performs analysis ---
    if character == "Vega Watt":
        domain = enriched.get("domain", "general")

        # If the story is technical, financial, legal, or DeFi,
        # Vega gives a booth-style “vibe” reaction instead of analysis.
        restricted_domains = [
            "ai", "defi", "venture", "markets", "macro",
            "onchain", "legal", "regulation", "security",
            "general", "news", "story"
        ]

        if domain in restricted_domains:
            # This replaces the summary with a vibe-only line.
            enriched["summary"] = "Whoa, that one’s above my pay grade, Chip — but the vibe in here is wild."

    summary = enriched.get("summary", "")
    headline = enriched.get("headline", "")
    sentiment = enriched.get("sentiment", "neutral").lower()
    importance = enriched.get("importance", 5)
    domain = enriched.get("domain", "general")

    if not profile:
        return f"{character} says: {summary}"

    style = profile.get("speaking_style", {})
    templates = profile.get("style_templates", {})

    openers = style.get("openers", [])
    connectors = style.get("connectors", [])
    closings = style.get("closings", [])
    tone_mods = style.get("tone_modifiers", [])

    emo_map = profile.get("emotional_tone_map", {})
    tone = emo_map.get(sentiment, emo_map.get("neutral", ""))

    opener = openers[0] if openers else ""
    connector = connectors[0] if connectors else ""
    closing = closings[0] if closings else ""
    tone_mod = tone_mods[0] if tone_mods else ""

    # Build an emotional sentence
    emotion_sentence = f"This feels {tone}."

    # Pick a template
    # (Later this becomes randomized)
    template = None
    if templates.get("studio"):
        template = templates["studio"][0]
    elif templates.get("simple"):
        template = templates["simple"][0]
    else:
        template = "{summary}"

    # Fill placeholders
    line = template.format(
        opener=opener,
        connector=connector,
        closing=closing,
        tone=tone,
        tone_mod=tone_mod,
        summary=summary,
        emotion_sentence=emotion_sentence
    )

    # Clean spacing and artifacts
    line = " ".join(line.split())
    line = line.replace(" .", ".").replace("..", ".")
    line = line.replace("( ", "(").replace(" )", ")")

    # ... existing logic that assembles `line` for any character ...

    line = f"{opener} {summary} {connector} {emotion_sentence}"

    # Chip Blue — route to new unified persona engine
    from character_brain.chip_persona import build_chip_line
    if character == "Chip Blue":
        return build_chip_line(enriched)
