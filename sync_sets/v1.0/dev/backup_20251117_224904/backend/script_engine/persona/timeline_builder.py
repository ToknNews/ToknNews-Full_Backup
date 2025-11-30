#!/usr/bin/env python3
"""
TOKNNews — Timeline Builder (Final PD-Integrated Build)
Module C-8
"""

import random
import time

# Absolute imports for stability
from script_engine.persona.line_builder import apply_tone_shift
from script_engine.persona.line_builder import (
    build_analysis_line,
    build_transition_line,
    build_vega_line,
    build_bitsy_interrupt,
    build_reaction_line
)
from backend.script_engine.character_brain.persona_loader import (
    get_voice
)


# ---------------------------------------------------------
# Utility blocks
# ---------------------------------------------------------

def _block(text, character, block_type):
    return {
        "type": block_type,
        "character": character,
        "voice_id": get_voice(character),
        "text": text,
        "timestamp": time.time()
    }


def _audio_block(text, character, block_type):
    return {
        "character": character,
        "voice_id": get_voice(character),
        "block_type": block_type,
        "text": text,                 # required for TTS
        "content": text,              # compatibility
        "timestamp": time.time()      # required for file naming & ordering
    }


# ---------------------------------------------------------
# MAIN — Build timeline based on PD instructions
# ---------------------------------------------------------

def build_timeline(
    character: str,
    headline: str,
    synthesis: str = "",
    article_context: str = "",
    anchors=None,
    allow_bitsy=False,
    allow_vega=False,
    show_intro=False,
    segment_type="headline",
    tone_shift=None
):

    timeline = []
    audio_blocks = []

    if anchors is None:
        anchors = ["reef", "lawson", "bond"]

    # ---------------------------------------------------------
    # SHOW INTRO (Vega voiceover + studio splash)
    # ---------------------------------------------------------
    if show_intro:
        intro_line = (
            "You're watching ToknNews — where the signal matters more than the noise."
        )
        timeline.append(_block(intro_line, "vega", "show_intro"))
        audio_blocks.append(_audio_block(intro_line, "vega", "show_intro"))

        # Chip hard cut-in after intro
        chip_intro = "Good evening — let's get into the first story."
        timeline.append(_block(chip_intro, "chip", "chip_open"))
        audio_blocks.append(_audio_block(chip_intro, "chip", "chip_open"))

    else:
        # Regular reaction-based Chip open
        chip_open = build_reaction_line("chip", headline, tone_shift=tone_shift)
        timeline.append(_block(chip_open, "chip", "chip_open"))
        audio_blocks.append(_audio_block(chip_open, "chip", "chip_open"))

    # ---------------------------------------------------------
    # CHIP ANALYSIS
    # ---------------------------------------------------------
    chip_analysis = build_analysis_line("chip", headline, synthesis, article_context, tone_shift=tone_shift)
    timeline.append(_block(chip_analysis, "chip", "chip_analysis"))
    audio_blocks.append(_audio_block(chip_analysis, "chip", "chip_analysis"))

    # ---------------------------------------------------------
    # ANCHOR CROSSTALK (PD-selected anchors)
    # ---------------------------------------------------------
    for anchor in anchors:
        toss = build_transition_line("chip", "anchor", tone_shift=tone_shift)
        timeline.append(_block(toss, "chip", "chip_toss"))
        audio_blocks.append(_audio_block(toss, "chip", "chip_toss"))

        # Persona-driven anchor reaction to Chip
        react = build_reaction_line(anchor, headline, tone_shift=tone_shift)
        timeline.append(_block(react, anchor, "anchor_react"))
        audio_blocks.append(_audio_block(react, anchor, "anchor_react"))

        a_line = build_analysis_line(anchor, headline, synthesis, None, tone_shift=tone_shift)
        timeline.append(_block(a_line, anchor, "anchor_analysis"))
        audio_blocks.append(_audio_block(a_line, anchor, "anchor_analysis"))

        # ---------------------------------------------------------
        # OPTIONAL: Anchor disagreement with previous anchor
        # Only triggers if:
        #   • more than one anchor
        #   • this is NOT the first anchor
        # ---------------------------------------------------------
        if len(anchors) > 1 and anchor != anchors[0]:
            dispute = f"Look, I’ve got to push back on {anchors[0].capitalize()} here — {synthesis or 'these numbers tell a different story.'}"
            dispute = apply_tone_shift(dispute, tone_shift)

            timeline.append(_block(dispute, anchor, "anchor_disagree"))
            audio_blocks.append(_audio_block(dispute, anchor, "anchor_disagree"))

    # ---------------------------------------------------------
    # VEGA (PD-controlled)
    # ---------------------------------------------------------
    if allow_vega:
        v_line = build_vega_line(headline, synthesis)
        timeline.append(_block(v_line, "vega", "vega_block"))
        audio_blocks.append(_audio_block(v_line, "vega", "vega_block"))

    # ---------------------------------------------------------
    # BITSY (PD-controlled)
    # ---------------------------------------------------------
    if allow_bitsy:
        bits = build_bitsy_interrupt()
        timeline.append(_block(bits, "bitsy", "bitsy_interrupt"))
        audio_blocks.append(_audio_block(bits, "bitsy", "bitsy_interrupt"))

    # ---------------------------------------------------------
    # CHIP RE-ENTRY (always)
    # ---------------------------------------------------------
    chip_re = build_transition_line("chip", "reentry", tone_shift=tone_shift)
    timeline.append(_block(chip_re, "chip", "chip_reentry"))
    audio_blocks.append(_audio_block(chip_re, "chip", "chip_reentry"))

    # ---------------------------------------------------------
    # CHIP OUTRO
    # ---------------------------------------------------------
    outro = "That's the latest — we'll continue tracking developments."
    timeline.append(_block(outro, "chip", "chip_outro"))
    audio_blocks.append(_audio_block(outro, "chip", "chip_outro"))

    # ---------------------------------------------------------
    # UNREAL METADATA (Final C-6)
    # ---------------------------------------------------------

    # Ordered characters
    character_list = []
    for b in timeline:
        if b["character"] not in character_list:
            character_list.append(b["character"])

    # Shot plan based on anchor count
    if len(anchors) > 1:
        camera_plan = "two_shot_chip_anchor"
        shot_plan = [
            {"shot": "chip_intro", "camera": "chip_close"},
            {"shot": "primary_analysis", "camera": "chip_mid"},
            {"shot": "anchor_1", "camera": "anchor_close"},
            {"shot": "anchor_2", "camera": "anchor_close"},
            {"shot": "vega", "camera": "chaos_cut"},
            {"shot": "bitsy", "camera": "bitsy_pop"},
            {"shot": "chip_reentry", "camera": "chip_mid"},
            {"shot": "outro", "camera": "chip_close"}
        ]
    else:
        camera_plan = "chip_single"
        shot_plan = [
            {"shot": "chip_intro", "camera": "chip_close"},
            {"shot": "primary_analysis", "camera": "chip_mid"},
            {"shot": "anchor_1", "camera": "anchor_close"},
            {"shot": "vega", "camera": "chaos_cut"},
            {"shot": "bitsy", "camera": "bitsy_pop"},
            {"shot": "chip_reentry", "camera": "chip_mid"},
            {"shot": "outro", "camera": "chip_close"}
        ]

    duration_seconds = max(5, len(timeline) * 3.2)

    audio_tracks = [
        {
            "character": b["character"],
            "voice_id": b["voice_id"],
            "text": b["text"],
            "block_type": b["type"],
            "timestamp": b["timestamp"]
        }
        for b in timeline
    ]

    unreal = {
        "scene_id": f"scene_{int(time.time())}",
        "engine_version": "UE5.3+",
        "camera_plan": camera_plan,
        "characters": character_list,
        "shot_plan": shot_plan,
        "audio_tracks": audio_tracks,
        "duration_seconds": duration_seconds
    }

    # ---------------------------------------------------------
    # FINAL RETURN
    # ---------------------------------------------------------
    return {
        "timeline": timeline,
        "audio_blocks": audio_blocks,
        "unreal": unreal
    }


# ---------------------------------------------------------
# Local test runner
# ---------------------------------------------------------

if __name__ == "__main__":
    sample = build_timeline(
        character="chip",
        headline="Solana ETF surge continues",
        synthesis="capital rotation into solana ecosystem",
        anchors=["reef", "lawson"],
        allow_bitsy=True,
        allow_vega=True,
        show_intro=True,
        segment_type="headline"
    )
    import json
    print(json.dumps(sample, indent=2))
