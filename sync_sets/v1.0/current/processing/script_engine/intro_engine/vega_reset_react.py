# intro_engine/vega_reset_react.py

def vega_reset_reaction(daypart):
    """
    Lightweight optional Vega reaction after Chip reset.
    Called only when reset is NOT serious.
    """
    lines = {
        "morning": "Quick breather — fresh start.",
        "afternoon": "Alright, realigning a bit.",
        "evening": "Let’s reset and keep moving.",
        "late_night": "Late reset — keeping it rolling.",
        "default": "Back in sync."
    }
    return lines.get(daypart, lines["default"])
