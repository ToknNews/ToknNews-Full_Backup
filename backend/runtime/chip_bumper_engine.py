#!/usr/bin/env python3
"""
chip_bumper_engine.py
TOKEN NEWS — Chip Bumper Engine (Static)

Chip uses these lines when:
 - resetting context
 - transitioning between major topics
 - reinforcing clarity ("big picture check")
 - pacing fills (runtime expansion)
"""

import random

# ============================================================
# CHIP RESET / BIG PICTURE BUMPERS
# ============================================================

CHIP_RESETS = [
    "Let’s reset the board for a moment.",
    "Zooming out, here’s the bigger picture.",
    "Let’s take a step back and ground this.",
    "Before we move on, here’s what truly matters.",
    "Resetting with some clarity now.",
    "Let’s orient ourselves for the next story.",
    "Here’s the broader context as we shift ahead.",
    "One quick reset before we pivot.",
    "Let’s make sure we’re aligned before we continue.",
    "Stepping back for a clearer view of where things stand."
]

# ============================================================
# CHIP TRANSITION BUMPERS
# ============================================================

CHIP_TRANSITIONS = [
    "Let’s shift into the next development.",
    "Moving ahead now.",
    "Here’s what’s next.",
    "Let’s continue the rundown.",
    "Transitioning now to the next major story.",
    "Let’s take a look at the next headline.",
    "Continuing coverage now.",
    "Let’s move the cycle forward.",
    "Next development coming up.",
    "Let’s keep the momentum going."
]


# ============================================================
# API
# ============================================================

def chip_reset_bumper() -> dict:
    text = random.choice(CHIP_RESETS)
    return {
        "speaker": "chip",
        "text": text,
        "block_type": "chip_reset"
    }


def chip_transition_bumper() -> dict:
    text = random.choice(CHIP_TRANSITIONS)
    return {
        "speaker": "chip",
        "text": text,
        "block_type": "chip_transition"
    }


def generate_chip_padding(kind: str = "reset") -> dict:
    """
    Used by pacing engine + runtime controller
    to expand runtime safely.
    """
    if kind == "reset":
        return chip_reset_bumper()
    return chip_transition_bumper()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":
    print("Reset:", chip_reset_bumper())
    print("Transition:", chip_transition_bumper())
