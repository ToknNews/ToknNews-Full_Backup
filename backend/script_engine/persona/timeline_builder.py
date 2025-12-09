#!/usr/bin/env python3
"""
timeline_builder_v5.py
ToknNews 2025 — Dynamic Conversational Timeline Builder

Key upgrades:
 - Dynamic turn-taking (Chip anchors the segment, but interplay is organic)
 - Persona interplay engine (NEWS vs LATENIGHT styles)
 - UE cue metadata injected per block
 - Integrated with editorial_engine_v4 enrichment
 - Flexible batching for GPT convos
"""

import time
import random
from backend.script_engine.persona.pd_engine import pd_engine
from backend.script_engine.grok_writer_v5 import generate_conversation
from backend.script_engine.runtime_estimator import estimate_block_runtime
from backend.script_engine.persona.voice_map import load_voice_map


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def _block(text, speaker, tag, cue=None):
    return {
        "speaker": speaker.lower(),
        "text": text,
        "tag": tag,
        "timestamp": time.time(),
        "cue": cue or {}
    }


def _audio_block(text, speaker, tag, voice_map, cue=None):
    return {
        "speaker": speaker.lower(),
        "voice_id": voice_map.get(speaker.lower(), voice_map.get("chip", "")),
        "text": text,
        "block_type": tag,
        "timestamp": time.time(),
        "cue": cue or {}
    }


def _cue_for(speaker, mode):
    """
    Minimal UE metadata (expand later).
    """
    if speaker == "chip":
        return {"camera": "chip_center", "emotion": "calm", "energy": 0.6}
    if speaker == "vega":
        return {"camera": "wide", "emotion": "upbeat", "energy": 0.8}
    if speaker == "bitsy":
        return {"camera": "closeup_fast", "emotion": "chaotic", "energy": 1.0}

    # generic for anchors
    return {"camera": "anchor_medium", "emotion": "neutral", "energy": 0.7}


# ------------------------------------------------------------
# Intro / Outro
# ------------------------------------------------------------

def _intro(mode, daypart):
    if mode == "BREAKING":
        return [
            ("vega", "vega_intro", "This is a ToknNews breaking update."),
            ("chip", "chip_intro", "We have urgent developments to cover.")
        ]

    if mode == "MORNING_BRIEF":
        return [
            ("vega", "vega_intro", "You're watching ToknNews."),
            ("chip", "chip_intro", "Good morning — here’s your quick briefing.")
        ]

    if mode == "CHAOS":
        return [
            ("vega", "vega_intro", "Late Edition is live — buckle up."),
            ("chip", "chip_intro", "Long night ahead. Let’s unpack the damage.")
        ]

    # Default NEWS
    return [
        ("vega", "vega_intro", "You're watching ToknNews."),
        ("chip", "chip_intro", f"Good {daypart}, here’s what’s moving.")
    ]


def _outro(mode):
    if mode == "BREAKING":
        return "This has been a ToknNews breaking update — more as it develops."
    if mode == "MORNING_BRIEF":
        return "That’s your morning briefing. See you next cycle."
    if mode == "CHAOS":
        return "ToknNews Late Edition — cope, seethe, and stay entertained."
    return "Thank you for watching ToknNews — we’ll see you next cycle."


# ------------------------------------------------------------
# MAIN PIPELINE
# ------------------------------------------------------------

def build_timeline(stories, *, daypart="evening", show_mode="NEWS", voice_map=None):
    voice_map = voice_map or load_voice_map()

    timeline = []
    audio_blocks = []
    est_runtime = 0.0

    # ---------------------------------
    # 1. PDv4 Story Routing
    # ---------------------------------
    pd_results = pd_engine(stories, mode=show_mode)

    # ---------------------------------
    # 2. INTRO
    # ---------------------------------
    for speaker, tag, text in _intro(show_mode, daypart):
        cue = _cue_for(speaker, show_mode)
        timeline.append(_block(text, speaker, tag, cue))
        audio_blocks.append(_audio_block(text, speaker, tag, voice_map, cue))
        est_runtime += estimate_block_runtime(tag, text, speaker)

    # ---------------------------------
    # 3. RUNDOWN (NEWS only)
    # ---------------------------------
    if show_mode in ("NEWS", "HEAVY_NEWS", "MORNING_BRIEF"):
        from backend.script_engine.dynamic_rundown import generate_rundown
        rundown_text = generate_rundown(stories, pd_results, daypart)

        cue = _cue_for("chip", show_mode)
        timeline.append(_block(rundown_text, "chip", "chip_rundown", cue))
        audio_blocks.append(_audio_block(rundown_text, "chip", "chip_rundown", voice_map, cue))
        est_runtime += estimate_block_runtime("chip_rundown", rundown_text, "chip")

    # ---------------------------------
    # 4. Conversational Segments
    # ---------------------------------
    for item in pd_results:
        story = item["story"]
        convo = generate_conversation(
            story=story,
            primary=item["primary"],
            secondary=item["secondary"],
            tertiary=item["tertiary"],
            mode=show_mode,
        )

        for turn in convo:
            speaker = turn["speaker"]
            text = turn["text"]
            tag = turn["tag"]

            cue = _cue_for(speaker, show_mode)

            timeline.append(_block(text, speaker, tag, cue))
            audio_blocks.append(_audio_block(text, speaker, tag, voice_map, cue))
            est_runtime += estimate_block_runtime(tag, text, speaker)

    # ---------------------------------
    # 5. OUTRO
    # ---------------------------------
    outro_text = _outro(show_mode)
    cue = _cue_for("chip", show_mode)

    timeline.append(_block(outro_text, "chip", "chip_outro", cue))
    audio_blocks.append(_audio_block(outro_text, "chip", "chip_outro", voice_map, cue))
    est_runtime += estimate_block_runtime("chip_outro", outro_text, "chip")

    # ---------------------------------
    # RETURN PACKAGE
    # ---------------------------------
    return {
        "blocks": timeline,
        "audio_blocks": audio_blocks,
        "estimated_runtime_sec": est_runtime,
        "pd_output": pd_results,
    }


if __name__ == "__main__":
    print("timeline_builder_v5 loaded.")
