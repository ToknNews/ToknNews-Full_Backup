# backend/script_engine/chip_reset/reset_builder.py

import random
from datetime import datetime
from ..time_logic import get_broadcast_time_info
from script_engine.intro_engine.chip_intro_enhancer import enhance_chip_intro
from script_engine.time_logic import get_broadcast_time_info
from script_engine.intro_engine.vega_reset_react import vega_reset_reaction


def build_chip_reset(stories):
    """
    Builds a mid-show reset block for Chip.
    """

    # --- Determine escalation BEFORE building the line ---
    escalation_level = stories[0].get("escalation_level", 0) if stories else 0

    # Base reset line
    if escalation_level >= 2:
        base = "We need to realign — things are moving quickly."
    else:
        base = "Let’s reset the board a bit."

    # Time + context
    ti = get_broadcast_time_info()
    daypart = ti.get("daypart")

    # Reset intros are neutral unless escalation is high
    dummy_story = {"sentiment": "neutral", "importance": 5}
    escalation = 0

    enhanced_intro = enhance_chip_intro(base, dummy_story, daypart, escalation)
    r1 = vega_reset_reaction(daypart)
    r2 = vega_reset_reaction(daypart)

    # Story rundown
    rundown_lines = []
    for s in stories:
        h = s.get("headline", "")
        rundown_lines.append(f"- {h}")

    return {
        "type": "chip_reset",
        "lines": [
            enhanced_intro,             # Chip enhanced intro
            r1,                # Vega calm reaction
            r2,                # Vega hyped reaction
            "Here’s what we’re tracking:\n" + "\n".join(rundown_lines)
        ]
    }

def build_reset_transition_line():
    """
    Chip uses this right after reset before tossing to analysis.
    Light, neutral, not repetitive.
    """
    lines = [
        "Alright — picking things back up.",
        "Back in motion — let’s dive in.",
        "Reset behind us — moving forward.",
        "Alright, let’s roll into the next piece.",
        "Good — now let’s keep it moving."
    ]
    import random
    return random.choice(lines)
