# backend/script_engine/director/daypart_rules.py

from datetime import datetime


def get_daypart() -> str:
    """
    Returns one of:
    'morning', 'day', 'evening', 'late_night', 'overnight'
    """

    hour = datetime.now().hour

    if 6 <= hour < 12:
        return "morning"
    if 12 <= hour < 17:
        return "day"
    if 17 <= hour < 22:
        return "evening"
    if 22 <= hour or hour < 2:
        return "late_night"
    return "overnight"
