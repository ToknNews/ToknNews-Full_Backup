#!/usr/bin/env python3

"""
time_logic.py
Provides time-of-day, daypart, and holiday detection for ToknNews.
Used by Chip’s greeting generator and toss engine.
"""

from datetime import datetime
import pytz

# Eastern Time zone
ET = pytz.timezone("US/Eastern")

# Mapping hour → greeting
GREETING_BY_HOUR = {
    range(5, 12): "Good morning",
    range(12, 17): "Good afternoon",
    range(17, 24): "Good evening",
    range(0, 5): "Good evening"  # Post-midnight still “evening style”
}

# Daypart mapping
DAYPART_RULES = {
    range(5, 12): "morning",
    range(12, 17): "afternoon",
    range(17, 22): "evening",
    range(22, 24): "late_night",
    range(0, 5): "late_night"
}

HOLIDAYS = {
    (1, 1): "Happy New Year",
    (7, 4): "Happy Fourth of July",
    (12, 25): "Merry Christmas",
    (11, 24): "Happy Thanksgiving"
}

def get_broadcast_time_info():
    """
    Returns:
    {
        "greeting": "Good morning",
        "holiday_name": "Merry Christmas" or None,
        "hour": 14,
        "daypart": "afternoon"
    }
    """

    now_et = datetime.now(ET)
    hour = now_et.hour

    # Greeting
    greeting = "Hello"
    for hours, text in GREETING_BY_HOUR.items():
        if hour in hours:
            greeting = text
            break

    # Daypart
    daypart = "evening"
    for hours, name in DAYPART_RULES.items():
        if hour in hours:
            daypart = name
            break

    # Holiday detection
    month_day = (now_et.month, now_et.day)
    holiday = HOLIDAYS.get(month_day)

    return {
        "greeting": greeting,
        "holiday_name": holiday,
        "hour": hour,
        "daypart": daypart
    }
