#!/usr/bin/env python3
"""
TOKNNews — Chip Opening Engine
Hybrid deterministic + GPT-enhanced version.
"""

import random
import datetime
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# Deterministic time checks
# -------------------------

def get_time_of_day():
    now = datetime.datetime.now()
    hour = now.hour
    if 4 <= hour < 12:
        return "morning"
    elif 12 <= hour < 17:
        return "afternoon"
    elif 17 <= hour < 22:
        return "evening"
    else:
        return "latenight"

def get_season():
    month = datetime.datetime.now().month
    if month in [1, 2, 3]:
        return "q1"
    elif month in [4, 5, 6]:
        return "q2"
    elif month in [7, 8, 9]:
        return "q3"
    else:
        return "q4"

def get_holiday():
    today = datetime.datetime.now().strftime("%m-%d")
    holiday_map = {
        "01-01": "new_year",
        "07-04": "independence_day",
        "11-23": "thanksgiving",  # Note: floating dates not handled
        "12-25": "christmas"
    }
    return holiday_map.get(today)

# -----------------------------------------
# Deterministic fallback greeting structure
# -----------------------------------------

DETERMINISTIC_OPENERS = {
    "morning": [
        "Good morning — here’s what you need to know.",
        "Good morning — markets are opening and headlines are rolling in."
    ],
    "afternoon": [
        "Good afternoon — let’s dive into the latest cycle.",
        "Good afternoon — developments are coming fast."
    ],
    "evening": [
        "Good evening — here’s what’s shaping markets.",
        "Good evening — let’s unpack what just happened."
    ],
    "latenight": [
        "Good evening — welcome to TOKN LateNight.",
        "Good evening — crypto doesn’t sleep and neither do we."
    ],
    "holiday": {
        "new_year": "It’s a fresh year — here’s what’s already moving.",
        "christmas": "Holiday markets are quiet but signals are emerging.",
        "thanksgiving": "Markets are paused but news never sleeps.",
        "independence_day": "Fireworks are coming — including on the charts."
    }
}

# ---------------------------------------------
# GPT-refined chip opener (OPTIONAL enhancement)
# ---------------------------------------------

def gpt_refine_chip_intro(line, time_of_day, season=None, holiday=None):
    try:
        holiday_line = f"It's {holiday.replace('_', ' ').title()}." if holiday else ""
        prompt = f"""
Chip is the rational lead anchor of TOKNNews. Refine the following greeting line for clarity, timing, and energy:

Input:
"{line}"

Context:
- Time of Day: {time_of_day}
- Season: {season}
- {holiday_line}

RULES:
- Sound like a calm, objective broadcaster
- NEVER repeat the headline
- Must be a single sentence
- Tone: professional, welcoming, clean
- Avoid slang, memes, or jokes
- Dry wit is acceptable

Output the cleaned line only.
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.7
        )

        return resp.choices[0].message.content.strip()

    except Exception as e:
        print("[ChipOpenEngine] GPT refine failed:", e)
        return line

# -------------------------------
# Public API: chip_open_line()
# -------------------------------

def chip_open_line(gpt_enabled=True):
    daypart = get_time_of_day()
    season = get_season()
    holiday = get_holiday()

    if holiday and holiday in DETERMINISTIC_OPENERS["holiday"]:
        base = DETERMINISTIC_OPENERS["holiday"][holiday]
    else:
        base = random.choice(DETERMINISTIC_OPENERS.get(daypart, DETERMINISTIC_OPENERS["morning"]))

    if gpt_enabled:
        return gpt_refine_chip_intro(base, daypart, season=season, holiday=holiday)

    return base
