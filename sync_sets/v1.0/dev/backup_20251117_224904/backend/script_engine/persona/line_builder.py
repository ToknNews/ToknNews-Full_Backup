#!/usr/bin/env python3
"""
TOKNNews — Persona Line Builder (Final Unified Version)
Includes:
 - Character Bible awareness
 - Tone routing integration
 - Safe fallbacks
 - Clean reusable utilities
"""

import random
import time

# Persona loader access
from script_engine.character_brain.persona_loader import (
    get_bible,
    get_voice,
    get_analysis_phrasing,
    get_analysis_structure,
    get_transition_phrasing,
    get_risk_phrasing,
    get_lexicon,
    get_rules
)

# ============================================================
# Tone Shift Modifier (PD-integrated)
# ============================================================
def apply_tone_shift(text: str, tone_shift: str):
    """
    PD tone shift modifier.
    tone_shift can be: 'calm', 'urgent', 'hype', 'serious', 'breaking'
    """
    if not tone_shift:
        return text

    mods = {
        "calm":       f"In a calmer tone, {text}",
        "urgent":     f"Urgent update — {text}",
        "hype":       f"Big energy — {text}",
        "serious":    f"On a serious note — {text}",
        "breaking":   f"Breaking now — {text}"
    }

    return mods.get(tone_shift, text)

# ---------------------------------------------------------
# UNIVERSAL TONE ROUTER
# ---------------------------------------------------------
def apply_routed_tone(character, tone_shift, line):
    """
    Applies PD tone routing using Character Bible:
    prefix, suffix, replacements, etc.
    """
    if not tone_shift:
        return line

    tone_profiles = get_bible(character).get("tone_profiles", {})
    profile = tone_profiles.get(tone_shift, tone_profiles.get("neutral", {}))

    if not profile:
        return line

    # Prefix
    if "prefix" in profile:
        line = profile["prefix"] + " " + line

    # Replacements
    for src, dst in profile.get("replacements", {}).items():
        line = line.replace(src, dst)

    # Suffix
    if "suffix" in profile:
        line = line + " " + profile["suffix"]

    return line


# ---------------------------------------------------------
# INTERNAL UTILS
# ---------------------------------------------------------
def _choose_safe(list_obj, default=""):
    if list_obj and isinstance(list_obj, list):
        return random.choice(list_obj)
    return default

def _safe_words(text):
    return " ".join(text.split())

def _apply_lexicon(character, text):
    lex = get_lexicon(character)
    avoid = lex.get("avoid", [])
    preferred = lex.get("preferred", [])

    for bad in avoid:
        if bad in text:
            text = text.replace(bad, "")
    return _safe_words(text)


# =========================================================
#  LINE BUILDERS
# =========================================================

# ---------------------------------------------------------
# CHIP / ANCHOR REACTION
# ---------------------------------------------------------
def build_reaction_line(character, headline, tone_shift=None):
    phrasing = get_analysis_phrasing(character)
    template = _choose_safe(phrasing, f"{character} reacts to the news.")

    line = template.replace("{headline}", headline)
    line = _apply_lexicon(character, line)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)


# ---------------------------------------------------------
# MAIN ANALYSIS LINES
# ---------------------------------------------------------
def build_analysis_line(character, headline, synthesis, article_context=None, tone_shift=None):
    structure = get_analysis_structure(character)
    template = _choose_safe(structure, "{synthesis}")

    line = template.replace("{headline}", headline)
    line = line.replace("{synthesis}", synthesis or "")
    line = line.replace("{context}", article_context or "")

    line = _apply_lexicon(character, line)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)


# ---------------------------------------------------------
# TRANSITION LINES
# ---------------------------------------------------------
def build_transition_line(character, target_group="anchor", tone_shift=None):
    phr = _choose_safe(
        get_transition_phrasing(character, target_group),
        f"{character} transitions to {target_group}."
    )

    line = _apply_lexicon(character, phr)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)


# ---------------------------------------------------------
# ANCHOR QUICK REACT
# ---------------------------------------------------------
def build_anchor_react(character, headline, tone_shift=None):
    phr = _choose_safe(
        get_analysis_phrasing(character),
        f"{character} gives their perspective."
    )
    line = phr.replace("{headline}", headline)

    line = _apply_lexicon(character, line)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)


# ---------------------------------------------------------
# VEGA — chaotic interludes
# ---------------------------------------------------------
def build_vega_line(headline, synthesis):
    return f"{synthesis or headline} — chaos mode engaged."


# ---------------------------------------------------------
# BITSY — random comedic pop-in
# ---------------------------------------------------------
def build_bitsy_interrupt():
    rules = get_rules("bitsy")
    lines = rules.get("phrasing", ["Oops! Bitsy presses a button."])
    return _choose_safe(lines)


# ---------------------------------------------------------
# CHIP RE-ENTRY (reset moment)
# ---------------------------------------------------------
def build_chip_reentry(character="chip", tone_shift=None):
    line = "Resetting with clarity:"
    return apply_routed_tone(character, tone_shift, line)
