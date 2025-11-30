# line_builder.py
# TOKEN NEWS — Deterministic Persona Fallback Line Builder
# --------------------------------------------------------------------
# GPT handles 99% of all line creation. This file exists ONLY as:
#   - A safety fallback if GPT times out
#   - A controllable "dev mode" lightweight generator
#   - A stub for local testing and debugging
#
# It should never override GPT output under normal operations.

import random
from script_engine.character_brain.persona_prompt_config import PERSONA_PROMPT_CONFIG


def safe_choice(options):
    """Return a safe random choice with fallback."""
    if not options:
        return ""
    return random.choice(options)


# =====================================================================
# FALLBACK: Persona Reaction Line
# =====================================================================

def fallback_reaction(persona: str, headline: str) -> str:
    """
    Deterministic fallback for a persona reacting to a headline.
    For emergency only when GPT is unavailable.
    """
    persona = persona.lower().strip()
    cfg = PERSONA_PROMPT_CONFIG.get(persona, {})

    # Prefer example lines (they’re closer to tone)
    examples = cfg.get("example_lines", [])
    if examples:
        return safe_choice(examples)

    # Or fallback to seed
    seed = cfg.get("gpt_prompt_seed", "")
    if seed:
        return seed

    return f"{persona.capitalize()} reacts to: {headline}"


# =====================================================================
# FALLBACK: Transition Line
# =====================================================================

GENERIC_TRANSITIONS = [
    "Let's move to the next story.",
    "Switching gears now.",
    "Here’s what else is unfolding.",
    "Let’s continue the rundown.",
    "Next headline coming in."
]

def fallback_transition(persona: str) -> str:
    """Fallback for transitions when GPT fails."""
    return safe_choice(GENERIC_TRANSITIONS)


# =====================================================================
# FALLBACK: Analysis Line
# =====================================================================

GENERIC_ANALYSIS = [
    "The implications here are significant.",
    "This development could shift sentiment noticeably.",
    "There are important structural dynamics at play.",
    "This introduces both risks and opportunities.",
    "The broader context helps explain the reaction."
]

def fallback_analysis(persona: str, headline: str) -> str:
    """
    Non-GPT analysis fallback — extremely generic to avoid identity drift.
    """
    persona = persona.lower().strip()
    cfg = PERSONA_PROMPT_CONFIG.get(persona, {})

    # Try persona-specific example lines first
    examples = cfg.get("example_lines", [])
    if examples:
        return safe_choice(examples)

    return safe_choice(GENERIC_ANALYSIS)


# =====================================================================
# EXPORTS
# =====================================================================

__all__ = [
    "fallback_reaction",
    "fallback_transition",
    "fallback_analysis",
]
