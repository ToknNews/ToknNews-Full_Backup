#!/usr/bin/env python3
"""
runtime_estimator.py
TOKEN NEWS — Runtime Estimator (2025)

Very lightweight estimator used by:
 - PD Engine v3
 - Timeline Builder v3
 - Ad Engine

Purpose:
Predict approximate runtime of a block WITHOUT asking GPT.
"""

# Hard-coded averages (in seconds) based on typical GPT output lengths
RUNTIME_WEIGHTS = {
    "vega_intro":     2,
    "chip_intro":     3,
    "chip_rundown":   8,
    "ad_read":        7,
    "chip_transition": 4,
    "anchor_analysis": 9,
    "duo_exchange":   7,
    "chip_outro":     4,
}

def estimate_block_runtime(tag: str) -> float:
    """
    Returns estimated runtime for a given block tag.
    Fallback is 6s for unknown types.
    """
    return RUNTIME_WEIGHTS.get(tag, 6.0)
