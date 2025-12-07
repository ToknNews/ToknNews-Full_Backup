#!/usr/bin/env python3
"""
timeline_builder_v4.py
ToknNews V2 — Timeline Builder using PDv4 (Rich Output)

Replaces timeline_builder_v3 completely.

Features:
 - PDv4 integration (primary / secondary / tertiary anchors)
 - Mode-aware formatting:
      BREAKING → 1 story, Chip + primary only
      MORNING_BRIEF → Chip-led, short blocks
      NEWS → primary + secondary
      HEAVY_NEWS → allow tertiary
      DEEP_DIVE → single-topic structured flow
      CHAOS → allow 3 anchors with playful dynamics
 - Batch GPT conversations
 - Tone cues passed to grok_writer
 - Hybrid runtime estimator
"""

import time
from backend.script_engine.persona.pd_engine import pd_engine
from backend.script_engine.grok_writer import write_batch_conversations
from backend.script_engine.dynamic_rundown import generate_rundown
from backend.script_engine.runtime_estimator import estimate_block_runtime
from backend.script_engine.persona.voice_map import load_voice_map


# ---------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------

def _block(text, speaker, tag):
    return {
        "speaker": speaker.lower(),
        "text": text,
        "tag": tag,
        "timestamp": time.time()
    }

def _audio_block(text, speaker, tag, voice_map):
    return {
        "speaker": speaker.lower(),
        "voice_id": voice_map.get(speaker.lower(), voice_map.get("chip","")),
        "text": text,
        "block_type": tag,
        "timestamp": time.time()
    }


# ---------------------------------------------------------------
# MODE-SPECIFIC INTRO STRUCTURES
# ---------------------------------------------------------------

def _intro_for_mode(mode, daypart):
    if mode == "BREAKING":
        return [
            ("vega", "vega_intro", "This is a ToknNews breaking update."),
            ("chip", "chip_intro", "We have urgent developments to cover.")
        ]
    if mode == "MORNING_BRIEF":
        return [
            ("vega", "vega_intro", "You're watching ToknNews."),
            ("chip", "chip_intro", "Good morning — here’s your quick rundown.")
        ]
    if mode == "CHAOS":
        return [
            ("vega", "vega_intro", "Welcome back to ToknNews Late Edition."),
            ("chip", "chip_intro", "It’s been one of those days — let’s break it down.")
        ]
    # Default NEWS intro
    return [
        ("vega", "vega_intro", "You're watching ToknNews."),
        ("chip", "chip_intro", f"Good {daypart}, welcome to ToknNews.")
    ]


# ---------------------------------------------------------------
# MODE-SPECIFIC OUTRO
# ---------------------------------------------------------------

def _outro_for_mode(mode):
    if mode == "BREAKING":
        return "This has been a ToknNews breaking update — more as it develops."
    if mode == "MORNING_BRIEF":
        return "That’s your morning briefing — see you next cycle."
    if mode == "CHAOS":
        return "ToknNews Late Edition — cope, seethe, and stay tuned."
    return "Thank you for watching ToknNews — we’ll see you next cycle."


# ---------------------------------------------------------------
# MAIN TIMELINE ENGINE
# ---------------------------------------------------------------

def build_timeline(stories, *, daypart="evening", show_mode="NEWS", voice_map=None):

    voice_map = voice_map or load_voice_map()
    timeline = []
    audio_blocks = []
    est_runtime = 0.0

    # -----------------------------------------------------------
    # PDv4 RICH OUTPUT
    # -----------------------------------------------------------
    pd_results = pd_engine(stories, mode=show_mode)

    # -----------------------------------------------------------
    # INTRO
    # -----------------------------------------------------------
    intro_struct = _intro_for_mode(show_mode, daypart)
    for speaker, tag, text in intro_struct:
        timeline.append(_block(text, speaker, tag))
        audio_blocks.append(_audio_block(text, speaker, tag, voice_map))
        est_runtime += estimate_block_runtime(tag, text, speaker)

    # -----------------------------------------------------------
    # RUNDOWN (NEWS family only)
    # -----------------------------------------------------------
    if show_mode in ("NEWS","HEAVY_NEWS","MORNING_BRIEF"):
        rundown_text = generate_rundown(stories, pd_results, daypart)
        timeline.append(_block(rundown_text, "chip", "chip_rundown"))
        audio_blocks.append(_audio_block(rundown_text, "chip", "chip_rundown", voice_map))
        est_runtime += estimate_block_runtime("chip_rundown", rundown_text, "chip")

    # -----------------------------------------------------------
    # BATCH GPT CONVERSATIONS
    # -----------------------------------------------------------
    BATCH = 5
    for idx in range(0, len(pd_results), BATCH):

        batch = pd_results[idx:idx+BATCH]

        # Prepare GPT batch payload
        gpt_in = []
        for item in batch:
            story    = item["story"]
            primary  = item["primary"]
            secondary= item["secondary"]
            tertiary = item["tertiary"]

            headline = story["headline"]
            summary  = story["summary"]

            # flatten participants for GPT
            anchors = [a for a in [primary, secondary, tertiary] if a]

            gpt_in.append({
                "headline": headline,
                "summary": summary,
                "primary": primary,
                "secondary": secondary,
                "tertiary": tertiary,
                "anchors": anchors
            })

        # Run GPT batch convo
        conversations = write_batch_conversations(gpt_in)

        # -------------------------------------------------------
        # SPLIT LINES INTO BLOCKS
        # -------------------------------------------------------
        for item, conv_text in zip(batch, conversations):

            anchors = item["anchors"]
            story   = item["story"]

            lines = [ln.strip() for ln in conv_text.splitlines() if ":" in ln]

            for j, raw in enumerate(lines):

                sp, txt = raw.split(":",1)
                speaker = sp.strip().lower()
                text    = txt.strip()

                # Tagging rules
                if j == 0 and speaker == "chip":
                    tag = "chip_transition"
                elif speaker in anchors:
                    tag = "anchor_analysis"
                else:
                    tag = "duo_exchange"

                timeline.append(_block(text, speaker, tag))
                audio_blocks.append(_audio_block(text, speaker, tag, voice_map))
                est_runtime += estimate_block_runtime(tag, text, speaker)

    # -----------------------------------------------------------
    # OUTRO
    # -----------------------------------------------------------
    outro_text = _outro_for_mode(show_mode)
    timeline.append(_block(outro_text, "chip", "chip_outro"))
    audio_blocks.append(_audio_block(outro_text, "chip", "chip_outro", voice_map))
    est_runtime += estimate_block_runtime("chip_outro", outro_text, "chip")

    # -----------------------------------------------------------
    # FINAL RETURN PACKAGE
    # -----------------------------------------------------------
    return {
        "blocks": timeline,
        "audio_blocks": audio_blocks,
        "estimated_runtime_sec": est_runtime,
        "pd_output": pd_results
    }


if __name__ == "__main__":
    print("timeline_builder_v4 loaded.")
