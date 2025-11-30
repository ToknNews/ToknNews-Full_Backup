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
"""

import sqlite3
import time
import os

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


# ======================================================================
# Database Setup
# ======================================================================

def init_mood_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
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

def clamp(val, low=0.0, high=1.0):
    return max(low, min(high, val))


def fetch_mood(persona: str) -> float:
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("SELECT value FROM persona_mood WHERE persona = ?", (persona,))
    row = c.fetchone()
    conn.close()

    if not row:
        return BASELINE_MOODS.get(persona, 0.2)

    return row[0]


def update_mood_value(persona: str, new_value: float):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute("""
        UPDATE persona_mood
        SET value = ?, last_update = ?
        WHERE persona = ?
    """, (new_value, time.time(), persona))

    conn.commit()
    conn.close()


# ======================================================================
# MOOD DRIFT ENGINE
# ======================================================================

def apply_pd_flags(persona: str, mood: float, pd_flags: dict) -> float:
    """Adjust mood based on Breaking News, volatility, social heat."""
    is_breaking = pd_flags.get("is_breaking", False)
    vol = pd_flags.get("volatility_risk", 0)
    heat = pd_flags.get("social_heat", 0)

    if is_breaking:
        # Breaking news → urgency boost, except for humor personas
        if persona not in ["bitsy", "rex"]:
            mood += 0.25

    # More volatility → higher energy
    mood += vol * 0.15

    # Social heat → caution for serious personas
    if persona in ["chip", "lawson", "neura", "bond"]:
        mood -= heat * 0.1
    else:
        mood += heat * 0.05

    return mood


def apply_daypart(persona: str, mood: float, daypart: str) -> float:
    """Daypart influences energy/expressiveness."""
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


def apply_memory_effect(persona: str, mood: float, memory_context: dict) -> float:
    """Memory influences emotional sharpness."""
    long_term = memory_context.get("long_term", [])

    for mem in long_term:
        strength = mem["strength"]
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
    pd_flags: dict,
    daypart: str,
    memory_context: dict
) -> float:
    """
    Apply all mood transforms, update SQLite, and return final mood value.
    """

    mood = fetch_mood(persona)

    # Apply influences:
    mood = apply_pd_flags(persona, mood, pd_flags)
    mood = apply_daypart(persona, mood, daypart)
    mood = apply_memory_effect(persona, mood, memory_context)

    # Decay toward baseline (prevents runaway mood)
    mood = decay_toward_baseline(persona, mood)

    # Clamp
    mood = clamp(mood, MIN_MOOD, MAX_MOOD)

    # Persist to DB
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
