#!/usr/bin/env python3
"""
runtime_estimator.py
ToknNews — Correct Hybrid Runtime Estimator (Block-Count Safe)
"""

# -------------------------
# PREVIEW MODE
# -------------------------

def estimate_preview_runtime(text: str, speaker: str, tag: str = "") -> float:
    """
    Accurate runtime estimator using characters-per-second logic.
    Prevents inflated runtimes when block count is large.
    """
    if not text:
        return 0.6

    t = text.strip()
    # 17 chars/sec is realistic for calm broadcast pacing
    sec = max(0.6, len(t) / 17.0)

    # Light adjustments
    if tag == "chip_transition":
        sec += 0.15
    elif tag == "anchor_analysis":
        sec += 0.05
    elif tag == "chip_outro":
        sec += 0.25

    return sec


# -------------------------
# TTS MODE
# -------------------------

def estimate_tts_runtime(audio_metadata: dict) -> float:
    if not isinstance(audio_metadata, dict):
        return None
    dur = audio_metadata.get("duration") or audio_metadata.get("audio_duration")
    if isinstance(dur, (int, float)):
        return max(0.1, float(dur))
    return None


# -------------------------
# PUBLIC API
# -------------------------

def estimate_block_runtime(tag: str, text: str = "", speaker: str = "", audio_metadata=None):
    tts_time = estimate_tts_runtime(audio_metadata)
    if tts_time is not None:
        return tts_time
    return estimate_preview_runtime(text, speaker, tag)
