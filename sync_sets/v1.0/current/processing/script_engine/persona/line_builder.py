#!/usr/bin/env python3

# ------------------------------------------------------------
# GLOBAL WRITER TOGGLE IMPORT (Package vs Local)
# ------------------------------------------------------------
try:
    from script_engine.engine_settings import USE_OPENAI_WRITER
except:
    from script_engine.openai_writer import gpt_analysis


# ------------------------------------------------------------
# OPENAI WRITER STUB FUNCTIONS (unused unless toggle = True)
# ------------------------------------------------------------
def generate_openai_reaction(character, headline, tone_shift):
    return None

def generate_openai_analysis(character, headline, synthesis, article_context, tone_shift):
    return None

def generate_openai_transition(character, target_group, tone_shift):
    return None

def generate_openai_anchor_react(character, headline, tone_shift):
    return None


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

# ------------------------------------------------------------
# GPT FALLBACK SAFETY — sanitize lines
# ------------------------------------------------------------
def _safe_gpt(text: str, fallback: str) -> str:
    if not text or not isinstance(text, str):
        return fallback
    cleaned = text.strip()
    if len(cleaned) == 0:
        return fallback
    return cleaned

# ------------------------------------------------------------
# Dual-Mode Imports (Package vs Local)
# ------------------------------------------------------------
try:
    from script_engine.character_brain.persona_loader import (
        get_bible,
        get_voice,
        get_analysis_phrasing,
        get_analysis_structure,
        get_transition_phrasing,
        get_risk_phrasing,
        get_lexicon,
        get_rules,
        get_domain
    )
except ImportError:
    from character_brain.persona_loader import (
        get_bible,
        get_voice,
        get_analysis_phrasing,
        get_analysis_structure,
        get_transition_phrasing,
        get_risk_phrasing,
        get_lexicon,
        get_rules,
        get_domain
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

# ------------------------------------------------------------
# REACTION LINE (toggle-aware)
# ------------------------------------------------------------
def build_reaction_line(character, headline, tone_shift=None):

    # --- OpenAI path ---
    if USE_OPENAI_WRITER:
        result = generate_openai_reaction(character, headline, tone_shift)
        if result:
            return result

    # --- Local fallback path ---
    phrasing = get_analysis_phrasing(character)
    template = _choose_safe(phrasing, f"{character} reacts to the news.")

    line = template.replace("{headline}", headline)
    line = _apply_lexicon(character, line)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)

# ------------------------------------------------------------
# ANALYSIS LINE (toggle-aware: GPT or Local)
# ------------------------------------------------------------
def build_analysis_line(character, headline, synthesis, article_context=None, tone_shift=None):

    # --- GPT writer path ---
    if USE_OPENAI_WRITER:
        try:
            from script_engine.openai_writer import gpt_analysis
        except ImportError:
            from openai_writer import gpt_analysis

        domain = get_domain(character)

        fallback_line = _safe_words(
            apply_routed_tone(
                character,
                tone_shift,
                _apply_lexicon(character, synthesis or "")
            )
        )

        result = gpt_analysis(
            character=character,
            headline=headline,
            synthesis=synthesis,
            domain=domain
        )

        return _safe_gpt(result, fallback_line)

    # --- Local fallback path ---
    structure = get_analysis_structure(character)
    template = _choose_safe(structure, "{synthesis}")

    line = template.replace("{headline}", headline)
    line = line.replace("{synthesis}", synthesis or "")
    line = line.replace("{context}", article_context or "")

    line = _apply_lexicon(character, line)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)

# ------------------------------------------------------------
# TRANSITION LINE (toggle-aware: GPT or Local)
# ------------------------------------------------------------
def build_transition_line(character, headline, brain, target_group="anchor", tone_shift=None, show_mode="news"):

    # --- GPT writer path ---
    if USE_OPENAI_WRITER:
        try:
            from script_engine.openai_writer import gpt_transition
        except ImportError:
            from openai_writer import gpt_transition

        domain = get_domain(character)

        # fallback if GPT returns bad output
        fallback_line = _safe_words(
            apply_routed_tone(
                character,
                tone_shift,
                _apply_lexicon(character, f"{character} transitions to {target_group}.")
            )
        )

        # call GPT

        result = gpt_transition(
            anchor=character,
            headline=headline,
            domain=domain,
            brain=brain,
            show_mode=show_mode
        )

        return _safe_gpt(result, fallback_line)

    # --- Local fallback path ---
    phr = get_transition_phrasing(character, target_group)
    template = _choose_safe(
        phr,
        f"{character} transitions to {target_group}."
    )

    line = template.replace("{target_group}", target_group)
    line = _apply_lexicon(character, line)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)

# ------------------------------------------------------------
# ANCHOR REACT (toggle-aware: GPT or Local)
# ------------------------------------------------------------
def build_anchor_react(character, headline, brain, tone_shift=None, show_mode="news"):

    # --- GPT writer path ---
    if USE_OPENAI_WRITER:
        try:
            from script_engine.openai_writer import gpt_anchor_react
        except ImportError:
            from openai_writer import gpt_anchor_react

        domain = get_domain(character)

        # Build fallback first
        fallback_line = _safe_words(
            apply_routed_tone(
                character,
                tone_shift,
                _apply_lexicon(character, f"{character} gives their perspective.")
            )
        )

        # Call GPT
        result = gpt_anchor_react(
            anchor=character,
            headline=headline,
            domain=domain,
            brain=brain,
            show_mode=show_mode
        )

        # Safe return
        return _safe_gpt(result, fallback_line)

    # --- Local fallback path ---
    phr = get_risk_phrasing(character)
    template = _choose_safe(
        phr,
        f"{character} gives their perspective."
    )

    line = template.replace("{headline}", headline)
    line = _apply_lexicon(character, line)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)

# ------------------------------------------------------------
# VEGA LINE (toggle-aware: GPT or Local)
# ------------------------------------------------------------
def build_vega_line(character, headline, brain, tone_shift=None, show_mode="news"):

    # --- GPT writer path ---
    if USE_OPENAI_WRITER:
        try:
            from script_engine.openai_writer import gpt_transition
        except ImportError:
            from openai_writer import gpt_transition

        domain = get_domain(character)

        # Vega's fallback tone is high-energy & musical
        fallback_line = _safe_words(
            apply_routed_tone(
                character,
                tone_shift,
                _apply_lexicon(character,
                    f"{character} sets the tone for what's next."
                )
            )
        )

        # Vega is a transition/energy character → use transition model
        result = gpt_transition(
            anchor=character,
            headline="",      # strip headline reference
            domain="vibe",
            brain=brain,
            show_mode="vibe"  # NEW MODE
        )

        return _safe_gpt(result, fallback_line)

    # --- Local fallback path ---
    template = "Resetting the vibe…"
    line = _apply_lexicon(character, template)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)

# ------------------------------------------------------------
# BITSY INTERRUPT (toggle-aware: GPT or Local)
# ------------------------------------------------------------
def build_bitsy_interrupt(character, headline, brain, tone_shift=None, show_mode="news"):
    """
    Bitsy = comedic relief / meta commentary.
    Uses gpt_transition with a special 'bitsy_meta' mode.
    Always lightweight. Never analytical.
    """

    # === GPT writer path ===
    if USE_OPENAI_WRITER:
        try:
            from script_engine.openai_writer import gpt_transition
        except ImportError:
            from openai_writer import gpt_transition

        # Bitsy uses her own persona domain
        domain = "sentiment"

        # Local fallback first (in case GPT fails completely)
        fallback_line = _safe_words(
            apply_routed_tone(
                character,
                tone_shift,
                _apply_lexicon(
                    character,
                    "Here’s the funny part…"
                )
            )
        )

        # GPT — use transition engine with Bitsy's special mode
        result = gpt_transition(
            anchor=character,
            headline=headline,
            domain=domain,
            brain=brain,
            show_mode="bitsy_meta"
        )

        return _safe_gpt(result, fallback_line)

    # === Local fallback path ===
    template = "Here’s the funny part…"
    line = _apply_lexicon(character, template)
    line = apply_routed_tone(character, tone_shift, line)

    return _safe_words(line)

# ---------------------------------------------------------
# CHIP RE-ENTRY (reset moment)
# ---------------------------------------------------------
def build_chip_reentry(character="chip", tone_shift=None):
    line = "Resetting with clarity:"
    return apply_routed_tone(character, tone_shift, line)
