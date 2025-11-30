# backend/script_engine/director/pacing_model.py

from datetime import datetime


def compute_energy_level(state) -> str:
    """
    Computes overall pacing/energy of the show based solely on time-of-day for now.
    Later this will include sentiment, cast fatigue, story density, etc.
    """

    hour = datetime.now().hour

    # Morning (moderate ramp-up)
    if 6 <= hour < 12:
        return "medium"

    # Daytime (professional, lower vibe)
    if 12 <= hour < 17:
        return "low"

    # Evening (stronger vibe, higher energy)
    if 17 <= hour < 22:
        return "medium_high"

    # Late night (highest energy window)
    if 22 <= hour or hour < 2:
        return "high"

    # Early morning (calm)
    return "low"
