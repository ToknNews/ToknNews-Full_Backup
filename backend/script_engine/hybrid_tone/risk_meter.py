#!/usr/bin/env python3
"""
TOKNNews — Risk Meter (Strict Deterministic Mode)
Provides a safe risk rating + optional adjustment note.
"""

def score_risk(text: str):
    """
    Returns:
        risk_level: "low" | "moderate" | "elevated"
        adjustment_line: brief deterministic phrase
    """

    if not text:
        return "moderate", ""

    lower = text.lower()

    # High-risk keywords
    if any(k in lower for k in ["crash", "lawsuit", "hack", "exploit", "liquidation", "collapse"]):
        return "elevated", "Risk conditions are elevated based on headline content."

    # Low-risk language
    if any(k in lower for k in ["growth", "increase", "expansion", "adoption"]):
        return "low", "Risk remains contained with constructive undertones."

    # Default
    return "moderate", ""
