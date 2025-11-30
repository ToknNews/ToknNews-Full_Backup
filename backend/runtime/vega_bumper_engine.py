#!/usr/bin/env python3
"""
vega_bumper_engine.py
TOKEN NEWS — Vega Bumper & Voiceover Engine

Provides polished Vega voiceover segments for:
 - Show intros
 - Segment transitions
 - Teasers ("Coming up next")
 - Runtime fillers for pacing engine

Integrates with:
 - scene_state.py
 - persona_style_overlay.py
 - persona_mood_model.py
"""

import random


# ======================================================================
# CANONICAL VEGA LINES
# ======================================================================

VEGA_INTROS = [
    "You're watching Token News — where the signal always cuts through the noise.",
    "Live from the booth — welcome back to Token News.",
    "This is Token News — let’s get into it.",
    "Good to have you with us — let’s dive into the cycle."
]

VEGA_TRANSITIONS = [
    "Let’s keep things moving.",
    "Staying with the momentum — next up.",
    "Back to the desk now.",
    "Shifting gears briefly before the next breakdown."
]

VEGA_TEASERS = [
    "Coming up next — a closer look at the market pressure.",
    "Stay tuned — the next segment goes deeper.",
    "Ahead — fresh insight on today’s biggest movers.",
    "Next up — a quick pulse check from the newsroom."
]

VEGA_OUTROS = [
    "Thanks for watching Token News — see you next cycle.",
    "Token News signing off — stay sharp out there.",
    "That’s the rundown — we’ll be back soon.",
    "Keep tracking the signal — Token News returns shortly."
]


# ======================================================================
# BUMPER GENERATORS
# ======================================================================

def vega_intro_bumper() -> dict:
    """Returns a Vega intro block."""
    text = random.choice(VEGA_INTROS)
    return {
        "speaker": "vega",
        "text": text,
        "block_type": "vega_intro"
    }


def vega_transition_bumper() -> dict:
    """Returns a Vega transition line."""
    text = random.choice(VEGA_TRANSITIONS)
    return {
        "speaker": "vega",
        "text": text,
        "block_type": "vega_transition"
    }


def vega_teaser_bumper() -> dict:
    """Returns a teaser line for pacing."""
    text = random.choice(VEGA_TEASERS)
    return {
        "speaker": "vega",
        "text": text,
        "block_type": "vega_teaser"
    }


def vega_outro_bumper() -> dict:
    """Returns a closing outro."""
    text = random.choice(VEGA_OUTROS)
    return {
        "speaker": "vega",
        "text": text,
        "block_type": "vega_outro"
    }


# ======================================================================
# RUNTIME PADDING API
# ======================================================================

def generate_runtime_padding(kind: str = "transition") -> dict:
    """
    Use this when pacing_engine needs natural runtime expansion
    without using ads.

    kind = "transition" | "teaser" | "intro" | "outro"
    """

    if kind == "intro":
        return vega_intro_bumper()

    if kind == "teaser":
        return vega_teaser_bumper()

    if kind == "outro":
        return vega_outro_bumper()

    # default “transition” filler
    return vega_transition_bumper()


# ======================================================================
# TEST
# ======================================================================
if __name__ == "__main__":
    print("Intro:", vega_intro_bumper())
    print("Transition:", vega_transition_bumper())
    print("Teaser:", vega_teaser_bumper())
    print("Outro:", vega_outro_bumper())
