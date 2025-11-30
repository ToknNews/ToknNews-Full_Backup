# intro_engine/chip_intro_enhancer.py

def enhance_chip_intro(base_intro, enriched, daypart, escalation_level):
    """
    Minimal enhancement layer for Chip’s intro.
    Adds tone only — no branching yet.
    """
    sentiment = enriched.get("sentiment", "neutral")
    importance = enriched.get("importance", 5)

    tone_fragments = []

    # Escalation emphasis
    if escalation_level >= 2:
        tone_fragments.append("Let's stay sharp.")

    # Daypart nuance
    if daypart == "late_night":
        tone_fragments.append("Long night ahead.")

    # Importance cue
    if importance >= 8:
        tone_fragments.append("Big development.")

    if tone_fragments:
        return f"{base_intro} {' '.join(tone_fragments)}"

    return base_intro
