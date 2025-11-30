# backend/script_engine/director/hijinx_rules.py

def determine_hijinx_level(daypart: str, sentiment: str | None, importance: int | None) -> str:
    """
    Minimal version of dynamic hijinx control.

    Returns one of:
        "none", "subtle", "moderate", "strong"

    High-level rules (stub):
    - If sentiment negative or importance high → no hijinx.
    - Daypart modifies what’s allowed.
    """

    # Serious story? No hijinx.
    if sentiment == "negative" or (importance is not None and importance >= 8):
        return "none"

    # Daypart rules
    if daypart == "day":
        return "subtle"
    if daypart == "evening":
        return "moderate"
    if daypart == "late_night":
        return "strong"
    if daypart == "morning":
        return "subtle"
    if daypart == "overnight":
        return "subtle"

    # Fallback
    return "subtle"
