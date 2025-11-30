# backend/script_engine/director/hijinx_engine.py

import random

VEGA_BOOTH_LINES = [
    "Vega (off-mic): \"Hey Chip, the vibe is immaculate tonight.\"",
    "Vega: \"You didn’t hear this from me, but somebody rewired the studio lights again.\"",
    "Vega: \"Booth check — everything’s spicy back here.\"",
    "Vega: \"Chip, keep an eye on the teleprompter. It just winked at me.\""
]

BITSY_LINES = [
    "Bitsy: \"Technically, that’s true — but let’s not pretend it’s the whole story.\"",
    "Bitsy: \"Just so the viewers know, this part gets complicated.\"",
    "Bitsy: \"Oh, we’re doing *that* angle? Bold choice.\"",
    "Bitsy: \"I ran those numbers — they check out.\""
]

def choose_hijinx_action(hijinx_level: str) -> str | None:
    """
    Stub: returns a single Vega booth hijinx moment.

    Later:
    - Bitsy meta moments
    - Anchor misdirection
    - Props
    - Mild chaos
    """

    if hijinx_level == "none":
        return None

    import random

    # 50% Vega, 50% Bitsy for moderate/strong hijinx
    if hijinx_level in ["moderate", "strong"]:
        if random.random() < 0.5:
            return random.choice(VEGA_BOOTH_LINES)
        else:
            return random.choice(BITSY_LINES)

    # Subtle hijinx: Bitsy only
    if hijinx_level == "subtle":
        return random.choice(BITSY_LINES[:2])

    # Fallback
    return random.choice(BITSY_LINES)
