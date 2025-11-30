# backend/script_engine/director/hijinx_rules.py

def should_trigger_hijinx(daypart: str,
                          sentiment: str | None = None,
                          importance: int | None = None) -> bool:
    """
    PD stub for hijinx allowance.
    Uses determine_hijinx_level() to decide if hijinx should fire.

    Returns True only for:
      - 'moderate' hijinx
      - 'strong' hijinx
    Never triggers for:
      - breaking news
      - negative sentiment
      - serious stories (importance >= 8)
    """

    level = determine_hijinx_level(daypart, sentiment, importance)

    # If it's a serious tone → disable hijinx entirely
    if level == "none":
        return False

    # PD 1.0 rule:
    # - Allow subtle hijinx only if daypart allows it
    # - Allow moderate/strong hijinx freely
    return level in ("moderate", "strong")

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
