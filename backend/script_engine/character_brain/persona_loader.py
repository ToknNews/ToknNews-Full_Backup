#!/usr/bin/env python3
"""
TOKNNews — Persona Loader (Module C-1)
Loads longform character personas from character_brain.json
and exposes deterministic access functions for the Script Engine.

This module provides:
 - load_persona(character)
 - get_voice(character)
 - get_analysis_phrasing(character)
 - get_transition_phrasing(character, target_group)
 - get_risk_phrasing(character)
 - get_lexicon(character)
 - get_cadence(character)
 - safe fallbacks
"""

import os
import json

BASE_DIR = os.path.dirname(__file__)
BRAIN_PATH = os.path.join(BASE_DIR, "character_brain.json")


# ---------------------------------------------------------
# Load persona brain once at import
# ---------------------------------------------------------

try:
    with open(BRAIN_PATH, "r", encoding="utf-8") as f:
        _BRAIN = json.load(f)
except Exception as e:
    print(f"[PersonaLoader] ERROR loading brain: {e}")
    _BRAIN = {}


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _safe(character: str) -> dict:
    """Return persona dict or safe fallback."""
    c = (character or "").lower()
    return _BRAIN.get(c, _BRAIN.get("chip", {}))


# ---------------------------------------------------------
# Public API
# ---------------------------------------------------------

def load_persona(character: str) -> dict:
    """
    Return full persona dictionary for given character.
    """
    return _safe(character)


def get_voice(character: str) -> str:
    """
    Returns ElevenLabs voice_id for the character.
    """
    p = _safe(character)
    return p.get("voice_id", "")


def get_persona_lines(character: str) -> list:
    """
    Longform persona description for prompting.
    """
    p = _safe(character)
    return p.get("persona", [])


def get_analysis_phrasing(character: str) -> list:
    """
    Returns preferred analysis phrases for this anchor.
    """
    p = _safe(character)
    style = p.get("analysis_style", {})
    return style.get("phrasing", [])


def get_analysis_structure(character: str) -> list:
    """
    Returns structural templates for Chip or others.
    """
    p = _safe(character)
    style = p.get("analysis_style", {})
    return style.get("structure", [])


def get_transition_phrasing(character: str, target_group: str = "anchor") -> list:
    """
    Get transition phrases:
      target_group = 'anchor' | 'vega' | 'reentry'
    """
    p = _safe(character)
    t = p.get("transition_style", {})
    if target_group == "vega":
        return t.get("to_vega", [])
    if target_group == "reentry":
        return t.get("reentry", [])
    return t.get("to_anchor", [])


def get_risk_phrasing(character: str) -> list:
    """
    Get risk-related phrasing.
    """
    p = _safe(character)
    r = p.get("risk_behavior", {})
    return r.get("phrasing", [])


def get_bias_profile(character: str) -> dict:
    """
    Return bias dictionary.
    """
    return _safe(character).get("bias", {})


def get_lexicon(character: str) -> dict:
    """
    Return preferred/avoid lexicon dict.
    """
    return _safe(character).get("lexicon", {})


def get_cadence(character: str) -> dict:
    """
    Return cadence rules: pacing, sentence style, energy.
    """
    return _safe(character).get("cadence", {})


def get_rules(character: str) -> dict:
    """
    Return special rules (Bitsy, Vega).
    """
    return _safe(character).get("rules", {})


# ---------------------------------------------------------
# Debug helper
# ---------------------------------------------------------

def debug_summary():
    """
    Print a simple summary for troubleshooting.
    """
    print("=== Persona Loader Summary ===")
    for key, p in _BRAIN.items():
        print(f"- {key} :: voice={p.get('voice_id','')}  persona_lines={len(p.get('persona',[]))}")


if __name__ == "__main__":
    debug_summary()
