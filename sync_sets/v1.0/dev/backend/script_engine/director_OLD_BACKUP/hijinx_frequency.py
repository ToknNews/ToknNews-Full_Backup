# backend/script_engine/director/hijinx_frequency.py

def hijinx_probability(daypart: str, sentiment: str | None, importance: int | None) -> float:
    """
    Returns a probability (0.0–1.0) for whether hijinx should occur at a segment boundary.

    Dynamic rules:
    - Serious news → 0.0
    - Daypart controls baseline
    """

    # No hijinx on serious or negative stories
    if sentiment == "negative" or (importance is not None and importance >= 7):
        return 0.0

    # Daypart-based probabilities
    if daypart == "day":         # business hours
        return 0.05              # 5%
    if daypart == "morning":
        return 0.10              # 10%
    if daypart == "evening":
        return 0.30              # 30%
    if daypart == "late_night":
        return 0.60              # 60%
    if daypart == "overnight":
        return 0.20              # 20%

    # fallback
    return 0.10
