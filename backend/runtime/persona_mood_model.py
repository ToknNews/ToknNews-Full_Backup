#!/usr/bin/env python3
"""
persona_mood_model.py
TOKEN NEWS — Persona Mood Drift Engine

Controls:
 - dynamic emotional state per persona
 - drift based on story context, PD flags, daypart
 - memory-influenced adjustments
 - slow decay toward baseline
 - exposes a global API for timeline + GPT engines

Moods influence persona style in persona_style_overlay.py.

NOTE:
- Uses WAL-safe SQLite connections via connect_sqlite() to avoid "database is locked".
"""

import time
import os
from typing import Dict

from backend.runtime.sqlite_utils import connect_sqlite

DB_PATH = "/opt/toknnews/data/persona_mood.db"

# ======================================================================
# MOOD BASELINES
# ======================================================================

# “0.0 = flat” → “1.0 = peak intensity”
BASELINE_MOODS = {
    "chip": 0.2,      # always calm
    "reef": 0.5,      # high energy baseline
    "lawson": 0.1,    # serious baseline
    "bond": 0.3,      # heavy tone baseline
    "ivy": 0.3,       # empathetic baseline
    "cash": 0.5,      # energetic + cynical baseline
    "ledger": 0.1,    # robotic baseline
    "penny": 0.25,    # warm baseline
    "bitsy": 0.7,     # naturally chaotic baseline
    "rex": 0.8,       # hyperbolic night volatility
    "neura": 0.2,     # analytical baseline
    "cap": 0.4,       # upbeat baseline
    "vega": 0.15      # smooth baseline
}

# Mood caps to prevent runaway amplification
MAX_MOOD = 1.0
MIN_MOOD = 0.0

# Persona sensitivity (how strongly a persona responds to PD flags)
# Higher = reacts more, lower = steadier.
PERSONA_SENSITIVITY = {
    "chip": 0.35,
    "lawson": 0.30,
    "neura": 0.35,
    "bond": 0.25,
    "ledger": 0.20,

    "ivy": 0.55,
    "penny": 0.55,
    "vega": 0.40,

    "cash": 0.80,
    "reef": 0.90,

    "bitsy": 1.05,
    "rex": 1.20,
    "cap": 0.70,
}


# ======================================================================
# Database Setup
# ======================================================================

def init_mood_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = connect_sqlite(DB_PATH)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS persona_mood (
        persona TEXT PRIMARY KEY,
        value REAL,
        last_update REAL
    );
    """)

    # Initialize entries if missing
    for persona, base in BASELINE_MOODS.items():
        c.execute("""
            INSERT OR IGNORE INTO persona_mood (persona, value, last_update)
            VALUES (?, ?, ?)
        """, (persona, base, time.time()))

    conn.commit()
    conn.close()


init_mood_db()


# ======================================================================
# Mood Helpers
# ======================================================================

def clamp(val: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, val))


def apply_inertia(old: float, new: float, factor: float = 0.7) -> float:
    """
    Smooth mood transitions.
    factor closer to 1.0 = more inertia (less change per update)
    """
    return old * factor + new * (1.0 - factor)


def fetch_mood(persona: str) -> float:
    conn = connect_sqlite(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT value FROM persona_mood WHERE persona = ?", (persona,))
    row = c.fetchone()
    conn.close()

    if not row:
        return BASELINE_MOODS.get(persona, 0.2)

    return float(row[0])


def update_mood_value(persona: str, new_value: float):
    conn = connect_sqlite(DB_PATH)
    c = conn.cursor()

    c.execute("""
        UPDATE persona_mood
        SET value = ?, last_update = ?
        WHERE persona = ?
    """, (float(new_value), time.time(), persona))

    conn.commit()
    conn.close()


# ======================================================================
# MOOD DRIFT ENGINE
# ======================================================================

def apply_pd_flags(persona: str, mood: float, pd_flags: Dict) -> float:
    """Adjust mood based on Breaking News, volatility, social heat."""
    is_breaking = bool(pd_flags.get("is_breaking", False))
    vol = float(pd_flags.get("volatility_risk", 0) or 0)
    heat = float(pd_flags.get("social_heat", 0) or 0)

    sensitivity = PERSONA_SENSITIVITY.get(persona, 0.5)

    if is_breaking:
        # Breaking → urgency boost, except humor personas handled by sensitivity
        mood += 0.25 * sensitivity

    # Volatility → energy
    mood += vol * 0.15 * sensitivity

    # Social heat → caution for serious personas, hype for playful personas
    if persona in ["chip", "lawson", "neura", "bond", "ledger"]:
        mood -= heat * 0.10 * sensitivity
    else:
        mood += heat * 0.05 * sensitivity

    return mood


def apply_daypart(persona: str, mood: float, daypart: str) -> float:
    """Daypart influences energy/expressiveness."""
    daypart = (daypart or "").lower().strip()

    if daypart == "morning":
        mood -= 0.05
    elif daypart == "afternoon":
        mood += 0.00
    elif daypart == "evening":
        mood += 0.05
    elif daypart == "latenight":
        if persona in ["rex", "bitsy"]:
            mood += 0.25
        else:
            mood += 0.10

    return mood


def apply_memory_effect(persona: str, mood: float, memory_context: Dict) -> float:
    """
    Memory influences emotional sharpness.
    Keeps behavior similar to your original, but safe on missing keys.
    """
    long_term = memory_context.get("long_term", []) or []

    for mem in long_term:
        strength = float(mem.get("strength", 0) or 0)
        # Running themes slightly amplify persona characteristics
        mood += 0.05 * strength

    return mood


def decay_toward_baseline(persona: str, mood: float) -> float:
    baseline = BASELINE_MOODS.get(persona, 0.2)
    return mood * 0.90 + baseline * 0.10


# ======================================================================
# MAIN API
# ======================================================================

def update_persona_mood(
    persona: str,
    pd_flags: Dict,
    daypart: str,
    memory_context: Dict
) -> float:
    """
    Apply all mood transforms, update SQLite, and return final mood value.
    """

    old_mood = fetch_mood(persona)

    mood = old_mood
    mood = apply_pd_flags(persona, mood, pd_flags or {})
    mood = apply_daypart(persona, mood, daypart or "")
    mood = apply_memory_effect(persona, mood, memory_context or {})

    # Decay toward baseline (prevents runaway mood)
    mood = decay_toward_baseline(persona, mood)

    # Clamp
    mood = clamp(mood, MIN_MOOD, MAX_MOOD)

    # Inertia smoothing (prevents jitter)
    mood = apply_inertia(old_mood, mood, factor=0.7)

    # Persist
    update_mood_value(persona, mood)

    return mood


# ======================================================================
# TEST
# ======================================================================
if __name__ == "__main__":
    test_pd = {"is_breaking": True, "volatility_risk": 0.4, "social_heat": 0.2}

    test_mem = {
        "recent": [{"speaker": "chip", "text": "Let's zoom out."}],
        "episode": {"theme": "volatility"},
        "long_term": [{"type": "quirk", "content": "Reef mocks bridge risk", "strength": 0.9}]
    }

    mood = update_persona_mood(
        persona="reef",
        pd_flags=test_pd,
        daypart="evening",
        memory_context=test_mem
    )

    print("Updated mood:", mood)
