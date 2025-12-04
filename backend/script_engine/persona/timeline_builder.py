#!/usr/bin/env python3
"""
timeline_builder_v3.py
TOKEN NEWS — Full Episode Timeline Builder (2025, PDv3 Architecture)

Responsibilities:
 - Execute PDv3 format decisions
 - Apply dynamic rundown
 - Call GPT conversation engine
 - Honor runtime targets
 - Integrate Ad Engine (ads disabled by default)
 - Maintain scene_state for continuity
 - Ensure correct anchor roles (primary / secondary / tertiary)
 - Keep Vega booth-only
"""

import time
import datetime

from backend.script_engine.director.pd_engine_v3 import pd_decide_format
from backend.script_engine.dynamic_rundown import generate_rundown
from backend.script_engine.ad_engine import maybe_insert_ad
from backend.script_engine.runtime_estimator import estimate_block_runtime
from backend.script_engine.grok_writer import write_block_conversation


# ============================================================
# HELPERS
# ============================================================

def _block(text, speaker, tag):
    return {
        "speaker": speaker.lower(),
        "text": text,
        "tag": tag,
        "timestamp": time.time(),
    }


def _audio_block(text, speaker, tag, voice_map):
    vmap = voice_map or {}
    return {
        "speaker": speaker.lower(),
        "voice_id": vmap.get(speaker.lower(), vmap.get("chip", "")),
        "text": text,
        "block_type": tag,
        "timestamp": time.time(),
    }


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def build_timeline(story_clusters, *, daypart="evening", show_mode="NEWS", voice_map=None):
    """
    Returns:
    {
        "blocks": [...],
        "audio_blocks": [...],
        "pd_context": {...},
        "estimated_runtime_sec": X
    }
    """

    timeline = []
    audio = []

    # ========================================================
    # 1. PD FORMAT DECISION
    # ========================================================
    pd_context = pd_decide_format(story_clusters)
    fmt = pd_context["format"]
    target_runtime = pd_context["target_runtime_sec"]

    # Keep a running estimated runtime
    estimated_runtime_sec = 0

    # Scene state (passed into GPT conv engine)
    scene_state = {
        "block_index": 0,
        "previous_line": None,
        "segment_type": None,
        "daypart": daypart,
        "show_mode": show_mode,
        "pd_flags": pd_context,
    }


    # ========================================================
    # 2. INTRO — VEGA + CHIP
    # ========================================================

    vega_intro = "You're watching ToknNews."
    timeline.append(_block(vega_intro, "vega", "vega_intro"))
    audio.append(_audio_block(vega_intro, "vega", "vega_intro", voice_map))
    estimated_runtime_sec += estimate_block_runtime("vega_intro")

    chip_intro = f"Good {daypart}, welcome to ToknNews."
    timeline.append(_block(chip_intro, "chip", "chip_intro"))
    audio.append(_audio_block(chip_intro, "chip", "chip_intro", voice_map))
    estimated_runtime_sec += estimate_block_runtime("chip_intro")

    scene_state["previous_line"] = {"speaker": "chip", "text": chip_intro}
    scene_state["block_index"] += 2


    # ========================================================
    # 3. RUNDOWN (Dynamic)
    # ========================================================
    rundown_text = generate_rundown(
        story_clusters=story_clusters,
        pd_context=pd_context,
        daypart=daypart,
    )

    timeline.append(_block(rundown_text, "chip", "chip_rundown"))
    audio.append(_audio_block(rundown_text, "chip", "chip_rundown", voice_map))
    estimated_runtime_sec += estimate_block_runtime("chip_rundown")

    scene_state["previous_line"] = {"speaker": "chip", "text": rundown_text}
    scene_state["block_index"] += 1


    # ========================================================
    # 4. AD INSERTION (PD + rules)
    # ========================================================
    ad_block = maybe_insert_ad(
        pd_context=pd_context,
        estimated_runtime_sec=estimated_runtime_sec,
        segment_index=1  # after rundown
    )

    if ad_block:
        timeline.append(ad_block)
        audio.append(_audio_block(ad_block["text"], "vega", "ad_read", voice_map))
        estimated_runtime_sec += estimate_block_runtime("ad_read")
        scene_state["block_index"] += 1


    # ========================================================
    # 5. STORY LOOPS — GPT CONVERSATION ENGINE
    # ========================================================

    for idx, story in enumerate(story_clusters[:6]):
        headline = story.get("headline", "")
        summary  = story.get("summary", "")
        domain   = story.get("domain", "general")
        anchors  = story.get("anchors", ["chip"])

        primary   = anchors[0]
        secondary = anchors[1] if len(anchors) > 1 else None
        tertiary  = pd_context.get("tertiary_anchor") if idx == 0 else None

        print(f"[TL DEBUG] Story {idx} domain={domain} anchors={story.get('anchors')} primary={primary} secondary={secondary}")

        # Only PD-authorized tertiary anchors
        if tertiary == primary or tertiary == secondary:
            tertiary = None

        participants = [primary]
        if secondary: participants.append(secondary)
        if tertiary:  participants.append(tertiary)

        scene_state["segment_type"] = "conversation"

        conv_text = write_block_conversation(
            primary     = primary,
            headline    = headline,
            synthesis   = summary,
            scene_state = scene_state,
            episode_id  = "episode",
            secondary   = secondary,
        )

        print(f"[TL DEBUG] conv for '{headline}' (first 120 chars): {conv_text[:120]!r}")

        # Split lines Chip: Hello
        lines = [ln.strip() for ln in conv_text.splitlines() if ":" in ln]

        for i, line in enumerate(lines):
            speaker, text = line.split(":", 1)
            speaker = speaker.strip().lower()
            text = text.strip().strip('"')

            # Determine tag classification
            if i == 0 and speaker == "chip":
                tag = "chip_transition"
            elif i == 0:
                tag = "anchor_analysis"
            elif i == 1:
                tag = "anchor_analysis"
            else:
                tag = "duo_exchange"

            timeline.append(_block(text, speaker, tag))
            audio.append(_audio_block(text, speaker, tag, voice_map))

            estimated_runtime_sec += estimate_block_runtime(tag)

            scene_state["previous_line"] = {"speaker": speaker, "text": text}
            scene_state["block_index"] += 1


        # PD Smart Ad Insertions (optional)
        ad_block = maybe_insert_ad(
            pd_context=pd_context,
            estimated_runtime_sec=estimated_runtime_sec,
            segment_index=idx + 2,
        )
        if ad_block:
            timeline.append(ad_block)
            audio.append(_audio_block(ad_block["text"], "vega", "ad_read", voice_map))
            estimated_runtime_sec += estimate_block_runtime("ad_read")
            scene_state["block_index"] += 1


    # ========================================================
    # 6. OUTRO — always CHIP
    # ========================================================

    outro = "Thanks for watching ToknNews — Cope. Seethe. Stack. It's your choice."
    timeline.append(_block(outro, "chip", "chip_outro"))
    audio.append(_audio_block(outro, "chip", "chip_outro", voice_map))
    estimated_runtime_sec += estimate_block_runtime("chip_outro")


    # ========================================================
    # RETURN PACKAGE
    # ========================================================
    return {
        "blocks": timeline,
        "audio_blocks": audio,
        "pd_context": pd_context,
        "estimated_runtime_sec": estimated_runtime_sec,
    }

