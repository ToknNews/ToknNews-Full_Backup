"""
anchor_emotion_profile.py

Defines per-anchor emotional permissions.
Used for validation only. Does not enforce language.
"""

ANCHOR_EMOTION_PROFILE = {
    "chip": {
        "max_intensity": "high",
        "allowed": [
            "measured",
            "confident",
            "skeptical",
            "urgent",
            "concerned"
        ],
        "disallowed": [
            "chaotic",
            "mocking",
            "edge_of_control"
        ]
    },
    "bitsy": {
        "max_intensity": "extreme",
        "allowed": [
            "playful",
            "sarcastic",
            "chaotic",
            "mocking",
            "disbelief",
            "shock"
        ],
        "disallowed": []
    },
    "reef": {
        "max_intensity": "high",
        "allowed": [
            "curious",
            "alert",
            "disbelief",
            "concerned"
        ],
        "disallowed": [
            "mocking",
            "chaotic"
        ]
    },
    "bond": {
        "max_intensity": "medium",
        "allowed": [
            "measured",
            "concerned",
            "skeptical"
        ],
        "disallowed": [
            "playful",
            "chaotic",
            "sarcastic"
        ]
    },
    "ledger": {
        "max_intensity": "medium",
        "allowed": [
            "measured",
            "curious",
            "alert"
        ],
        "disallowed": [
            "mocking",
            "chaotic",
            "sarcastic"
        ]
    },
    "vega": {
        "max_intensity": "extreme",
        "allowed": [
            "confident",
            "urgent",
            "excited",
            "disbelief",
            "playful",
            "sarcastic",
            "alarm",
            "shock"
        ],
        "disallowed": [
            "edge_of_control"
        ]
    }
}
