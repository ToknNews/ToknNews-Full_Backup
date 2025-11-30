# backend/script_engine/director/cast_fatigue.py

def compute_cast_fatigue(cast_usage: dict[str, int]) -> dict[str, str]:
    """
    Stub:
    Returns a simple fatigue level for each cast member.

    usage < 5   → "low"
    5–10        → "medium"
    >10         → "high"
    """

    fatigue = {}

    for cast, usage in cast_usage.items():
        if usage > 10:
            fatigue[cast] = "high"
        elif usage > 5:
            fatigue[cast] = "medium"
        else:
            fatigue[cast] = "low"

    return fatigue
