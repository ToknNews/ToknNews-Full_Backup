#!/usr/bin/env python3
"""
timeline_builder_v5.py — ToknNews 2025
Full rewrite for Editorial Engine v4 + GrokWriter v5

Upgrades:
- Integrates editorial_engine_v4 output
- Uses generate_conversation() (multi-turn dialog)
- Mode-aware intros (NEWS, MORNING, BREAKING, CHAOS/latenight)
- Smooth pacing: transitions, setups, conclusions
- Persona interplay lines (anchors respond to each other)
- Produces timeline blocks + audio_blocks for rendering engine
"""

import time
from typing import List, Dict, Any

from backend.script_engine.persona.pd_engine_v45 import pd_engine
from backend.script_engine.grok_writer_v5 import generate_conversation
from script_engine.persona.voice_map import load_voice_map
from script_engine.dynamic_rundown import generate_rundown
from script_engine.runtime_estimator import estimate_block_runtime


# -------------------------------------------------------
# TIMELINE BLOCK HELPERS
# -------------------------------------------------------

def _block(text: str, speaker: str, tag: str):
    return {
        "speaker": speaker.lower(),
        "text": text,
        "tag": tag,
        "timestamp": time.time()
    }


def _audio_block(text: str, speaker: str, tag: str, voice_map: dict):
    return {
        "speaker": speaker.lower(),
        "voice_id": voice_map.get(speaker.lower(), voice_map.get("chip")),
        "text": text,
        "block_type": tag,
        "timestamp": time.time()
    }


# -------------------------------------------------------
# MODE-SPECIFIC INTRO + OUTRO
# -------------------------------------------------------

def _intro(mode: str, daypart: str):
    if mode == "BREAKING":
        return [
            ("vega",  "vega_intro", "This is a breaking update on ToknNews."),
            ("chip",  "chip_intro", "We’re tracking a fast-moving development.")
        ]

    if mode == "MORNING_BRIEF":
        return [
            ("vega", "vega_intro", "You're watching ToknNews."),
            ("chip", "chip_intro", "Good morning — here’s your concise market rundown.")
        ]

    if mode == "CHAOS":
        return [
            ("vega", "vega_intro", "ToknNews Late Edition — let's embrace the chaos."),
            ("chip", "chip_intro", "Long day — lots moving. Let’s take this apart.")
        ]

    # Standard NEWS intro
    return [
        ("vega", "vega_intro", "You're watching ToknNews."),
        ("chip", "chip_intro", f"Good {daypart}, let’s get into the top stories.")
    ]


def _outro(mode: str):
    if mode == "BREAKING":
        return "This has been a breaking update — more as details emerge."
    if mode == "MORNING_BRIEF":
        return "That wraps your morning briefing — see you next cycle."
    if mode == "CHAOS":
        return "ToknNews Late Edition — good luck out there."
    return "Thanks for watching ToknNews — see you next cycle."


# -------------------------------------------------------
# MAIN BUILDER — TIMELINE v5
# -------------------------------------------------------

def build_timeline(
    stories: List[Dict[str, Any]],
    *,
    daypart="evening",
    show_mode="NEWS",
    voice_map=None
):
    """
    stories: list of enriched story dicts from Editorial Engine v4
    """

    voice_map = voice_map or load_voice_map()

    timeline = []
    audio_blocks = []
    est_runtime = 0.0

    # ---------------------------------------------------
    # Primary anchor assignment from PD Engine v4
    # ---------------------------------------------------
    pd_results = pd_engine(stories, mode=show_mode)

    # ---------------------------------------------------
    # INTRO BLOCKS
    # ---------------------------------------------------
    for speaker, tag, text in _intro(show_mode, daypart):
        timeline.append(_block(text, speaker, tag))
        audio_blocks.append(_audio_block(text, speaker, tag, voice_map))
        est_runtime += estimate_block_runtime(tag, text, speaker)

    # ---------------------------------------------------
    # RUNDOWN (NEWS / MORNING / HEAVY_MODES)
    # ---------------------------------------------------
    if show_mode in ("NEWS", "HEAVY_NEWS", "MORNING_BRIEF"):
        rundown = generate_rundown(stories, pd_results, daypart)
        timeline.append(_block(rundown, "chip", "chip_rundown"))
        audio_blocks.append(_audio_block(rundown, "chip", "chip_rundown", voice_map))
        est_runtime += estimate_block_runtime("chip_rundown", rundown, "chip")

    # ---------------------------------------------------
    # MAIN STORY LOOPS
    # ---------------------------------------------------
    for item in pd_results:

        story = item["story"]
        primary = item["primary"]
        secondary = item.get("secondary")
        tertiary = item.get("tertiary")

        # ---- GPT conversation for this story ----
        convo = generate_conversation(
            story=story,
            primary=primary,
            secondary=secondary,
            tertiary=tertiary,
            mode=show_mode
        )

        # ---- Convert to timeline + audio blocks ----
        for j, line in enumerate(convo):
            speaker = line["speaker"]
            text = line["text"]

            # Stronger first-block tag
            tag = (
                "chip_transition" if j == 0 and speaker == "chip"
                else "anchor_analysis"
            )

            timeline.append(_block(text, speaker, tag))
            audio_blocks.append(_audio_block(text, speaker, tag, voice_map))
            est_runtime += estimate_block_runtime(tag, text, speaker)

    # ---------------------------------------------------
    # OUTRO BLOCK
    # ---------------------------------------------------
    outro_text = _outro(show_mode)
    timeline.append(_block(outro_text, "chip", "chip_outro"))
    audio_blocks.append(_audio_block(outro_text, "chip", "chip_outro", voice_map))
    est_runtime += estimate_block_runtime("chip_outro", outro_text, "chip")

    # ---------------------------------------------------
    # FINAL PACKAGE
    # ---------------------------------------------------
    return {
        "blocks": timeline,
        "audio_blocks": audio_blocks,
        "estimated_runtime_sec": est_runtime,
        "pd_output": pd_results
    }


if __name__ == "__main__":
    print("timeline_builder_v5 loaded.")
