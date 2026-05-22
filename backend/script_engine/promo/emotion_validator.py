"""
emotion_validator.py

Validation helpers for promo emotional configuration.
Pure validation only — no side effects, no persistence.
"""

from typing import Tuple

from backend.script_engine.promo.emotion_envelope import EMOTION_ENVELOPE
from backend.script_engine.promo.anchor_emotion_profile import ANCHOR_EMOTION_PROFILE


INTENSITY_ORDER = ["low", "medium", "high", "extreme"]


def _emotion_exists(emotion: str) -> bool:
    for bucket in EMOTION_ENVELOPE.values():
        if emotion in bucket:
            return True
    return False


def _bucket_for_emotion(emotion: str) -> str:
    for level, emotions in EMOTION_ENVELOPE.items():
        if emotion in emotions:
            return level
    raise ValueError(f"Unknown emotion: {emotion}")


def validate_emotion_config(
    anchor: str,
    emotion: str,
    intensity: float
) -> Tuple[bool, str]:
    """
    Validates whether an anchor is allowed to express a given emotion
    at the requested intensity.

    Returns:
        (True, "ok") or (False, reason)
    """

    # Anchor existence
    if anchor not in ANCHOR_EMOTION_PROFILE:
        return False, f"Unknown anchor: {anchor}"

    profile = ANCHOR_EMOTION_PROFILE[anchor]

    # Emotion existence
    if not _emotion_exists(emotion):
        return False, f"Unknown emotion: {emotion}"

    # Anchor permission
    if emotion in profile.get("disallowed", []):
        return False, f"Emotion '{emotion}' disallowed for anchor '{anchor}'"

    if emotion not in profile.get("allowed", []):
        return False, f"Emotion '{emotion}' not permitted for anchor '{anchor}'"

    # Intensity bounds
    if not (0.0 <= intensity <= 1.0):
        return False, "Intensity must be between 0.0 and 1.0"

    # Intensity ceiling by anchor
    emotion_bucket = _bucket_for_emotion(emotion)
    anchor_ceiling = profile["max_intensity"]

    if INTENSITY_ORDER.index(emotion_bucket) > INTENSITY_ORDER.index(anchor_ceiling):
        return (
            False,
            f"Emotion level '{emotion_bucket}' exceeds max intensity "
            f"'{anchor_ceiling}' for anchor '{anchor}'"
        )

    return True, "ok"
