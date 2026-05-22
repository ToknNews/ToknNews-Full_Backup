#!/usr/bin/env python3
"""
timeline_builder_v5.py — ToknNews 2025 (ESL-FIRST PATCH)

Authoritative timeline builder for:
- ESL v2 segments
- PD Engine v4.6
- Broadcast-realistic pacing
"""

import time
from typing import List, Dict, Any

from backend.script_engine.director.pd_engine_v46 import pd_engine
from backend.script_engine.grok_writer_v6 import generate_conversation
from backend.script_engine.persona.voice_map import load_voice_map
from backend.script_engine.runtime_estimator import estimate_block_runtime


# ============================================================
# BLOCK HELPERS
# ============================================================

def _block(text: str, speaker: str, tag: str):
    return {
        "speaker": speaker,
        "text": text.strip(),
        "tag": tag,
        "timestamp": time.time(),
    }


def _audio_block(text: str, speaker: str, tag: str, voice_map: dict):
    return {
        "speaker": speaker,
        "voice_id": voice_map.get(speaker, voice_map["chip"]),
        "text": text.strip(),
        "block_type": tag,
        "timestamp": time.time(),
    }


# ============================================================
# INTRO / OUTRO
# ============================================================

def build_intro(mode: str, daypart: str):
    if mode == "BREAKING":
        return [
            ("vega", "vega_intro", "This is a breaking update on ToknNews."),
            ("chip", "chip_intro", "We’re tracking a fast-moving development."),
        ]

    return [
        ("vega", "vega_intro", "You're watching ToknNews."),
        ("chip", "chip_intro", f"Good {daypart}, let’s get into the top stories."),
    ]


def build_outro(mode: str):
    if mode == "BREAKING":
        return "This has been a breaking update — more as details emerge."
    return "Thanks for watching ToknNews — see you next cycle."


# ============================================================
# MAIN BUILDER
# ============================================================

def build_timeline(
    segments: List[Dict[str, Any]],
    *,
    show_mode: str = "NEWS",
    daypart: str = "evening",
    voice_map: dict | None = None,
):
    """
    Input: ESL v2 segments
    Output: timeline blocks + audio blocks
    """

    voice_map = voice_map or load_voice_map()

    timeline = []
    audio_blocks = []
    est_runtime = 0.0

    # --------------------------------------------------
    # PD ENGINE (DOMAIN-CORRECT)
    # --------------------------------------------------
    pd_packets = pd_engine(segments, mode=show_mode, latenight=(show_mode == "CHAOS"))

    # --------------------------------------------------
    # INTRO
    # --------------------------------------------------
    for speaker, tag, text in build_intro(show_mode, daypart):
        timeline.append(_block(text, speaker, tag))
        audio_blocks.append(_audio_block(text, speaker, tag, voice_map))
        est_runtime += estimate_block_runtime(tag, text, speaker)

    # --------------------------------------------------
    # SEGMENT LOOPS
    # --------------------------------------------------
    for pkt in pd_packets:
        seg = pkt["story"]
        anchors = pkt["anchors"]

        thesis = seg.get("thesis", "")
        facts = seg.get("facts", [])
        implication = seg.get("implication", "")
        max_runtime = seg.get("pd_hints", {}).get("max_runtime_sec", 45)

        # ---------- PRIMARY: Thesis ----------
        primary = anchors[0]
        timeline.append(_block(thesis, primary, "segment_thesis"))
        audio_blocks.append(_audio_block(thesis, primary, "segment_thesis", voice_map))
        est_runtime += estimate_block_runtime("segment_thesis", thesis, primary)

        # ---------- FACT PASS (OPTIONAL) ----------
        for fact in facts[:2]:
            if est_runtime >= max_runtime:
                break
            timeline.append(_block(fact, primary, "segment_fact"))
            audio_blocks.append(_audio_block(fact, primary, "segment_fact", voice_map))
            est_runtime += estimate_block_runtime("segment_fact", fact, primary)

        # ---------- SECONDARY REACTION ----------
        if len(anchors) >= 2:
            secondary = anchors[1]
            reaction = generate_conversation(
                story=seg,
                primary=primary,
                secondary=secondary,
                tertiary=None,
                mode=show_mode,
                reaction_only=True,
            )[0]["text"]

            timeline.append(_block(reaction, secondary, "anchor_reaction"))
            audio_blocks.append(_audio_block(reaction, secondary, "anchor_reaction", voice_map))
            est_runtime += estimate_block_runtime("anchor_reaction", reaction, secondary)

        # ---------- CHIP WRAP (ONLY IF NEEDED) ----------
        if primary != "chip" and implication:
            timeline.append(_block(implication, "chip", "segment_wrap"))
            audio_blocks.append(_audio_block(implication, "chip", "segment_wrap", voice_map))
            est_runtime += estimate_block_runtime("segment_wrap", implication, "chip")

    # --------------------------------------------------
    # OUTRO
    # --------------------------------------------------
    outro = build_outro(show_mode)
    timeline.append(_block(outro, "chip", "chip_outro"))
    audio_blocks.append(_audio_block(outro, "chip", "chip_outro", voice_map))
    est_runtime += estimate_block_runtime("chip_outro", outro, "chip")

    # --------------------------------------------------
    # FINAL PACKAGE
    # --------------------------------------------------
    return {
        "blocks": timeline,
        "audio_blocks": audio_blocks,
        "estimated_runtime_sec": est_runtime,
    }


if __name__ == "__main__":
    print("timeline_builder_v5 (ESL-first) loaded.")
