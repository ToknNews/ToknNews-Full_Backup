"""
emotion_envelope.py

Defines the full expressive range allowed for promo content.
Derived-only. No persistence. No analytics binding.
"""

EMOTION_ENVELOPE = {
    "low": [
        "measured",
        "skeptical",
        "curious",
        "reserved"
    ],
    "medium": [
        "confident",
        "concerned",
        "alert",
        "engaged",
        "dry_humor"
    ],
    "high": [
        "urgent",
        "excited",
        "disbelief",
        "frustrated",
        "playful",
        "sarcastic"
    ],
    "extreme": [
        "alarm",
        "shock",
        "chaotic",
        "mocking",
        "edge_of_control"
    ]
}
