# backend/script_engine/chip_reset/reset_transitions.py

import random

RESET_RETURN_LINES = [
    "Alright — let’s get back into it.",
    "Let’s pick this up from here.",
    "Alright, back to it.",
    "Let’s keep moving.",
    "Now, let’s get back into the flow."
]

def build_reset_return_line():
    return random.choice(RESET_RETURN_LINES)
