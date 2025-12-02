#!/usr/bin/env python3
"""
timeline_builder.py
TOKEN NEWS — PHASE 2 (Post-writer Purge)

Responsibilities:
 - Build full AI-generated episode timeline
 - Enforce structure: Vega → Chip → Rundown → Stories → Outro
 - Maintain conversational continuity using scene_state
 - Activate duo exchanges on high-heat domains only
"""

import time
from backend.script_engine.director.pd_controller import run_pd
from backend.script_engine.grok_writer import write_block_conversation

# ============================================================
# Constants
# ============================================================

HIGH_HEAT_DOMAINS = {"macro", "markets", "regulation", "defi", "onchain", "ai"}

def should_enable_duo(domain: str) -> bool:
    return domain in HIGH_HEAT_DOMAINS

def _block(text, speaker, tag):
    return {
        "speaker": speaker,
        "text": text,
        "tag": tag,
        "timestamp": time.time()
    }

def _audio_block(text, speaker, tag, voice_map):
    return {
        "speaker": speaker,
        "voice_id": voice_map.get(speaker, voice_map.get("chip", "")),
        "text": text,
        "block_type": tag,
        "timestamp": time.time()
    }

def make_micro_headline(headline: str) -> str:
    words = headline.split()
    if len(words) <= 12:
        return headline
    return " ".join(words[:12]) + "…"

# ============================================================
# Primary Entry Point (matches CLI expectations)
# ============================================================

def build_timeline(story_clusters, voice_map, daypart):
    timeline = []
    audio = []
    scene_state = {
        "block_index": 0,
        "previous_line": None,
        "segment_type": "intro"
    }

    # === VEGA INTRO
    vega_intro = "You're watching Token News."
    timeline.append(_block(vega_intro, "vega", "vega_intro"))
    audio.append(_audio_block(vega_intro, "vega", "vega_intro", voice_map))
    scene_state["previous_line"] = {"speaker": "vega", "text": vega_intro}
    scene_state["block_index"] += 1

    # === CHIP INTRO
    chip_intro = f"Good {daypart}, welcome to Token News."
    timeline.append(_block(chip_intro, "chip", "chip_intro"))
    audio.append(_audio_block(chip_intro, "chip", "chip_intro", voice_map))
    scene_state["previous_line"] = {"speaker": "chip", "text": chip_intro}
    scene_state["block_index"] += 1

    # === RUNDOWN
    micro = [make_micro_headline(item["headline"]) for item in story_clusters[:6]]
    rundown_text = "Here’s what’s ahead:\n" + "\n".join(f"• {m}" for m in micro)
    timeline.append(_block(rundown_text, "chip", "chip_rundown"))
    audio.append(_audio_block(rundown_text, "chip", "chip_rundown", voice_map))
    scene_state["previous_line"] = {"speaker": "chip", "text": rundown_text}
    scene_state["block_index"] += 1

    # === STORIES
    for idx, story in enumerate(story_clusters[:6]):
        headline = story["headline"]
        summary  = story.get("summary", "")
        domain   = story.get("domain", "general")
        anchors  = story.get("anchors", ["chip"])
        primary  = anchors[0]
        secondary = anchors[1] if len(anchors) > 1 else None

        pd_cfg = run_pd(
            headline         = headline,
            suggested_anchor = primary,
            story_index      = idx,
            total_stories    = len(story_clusters)
        )
        scene_state["pd_flags"] = pd_cfg

        # === High-heat: run duo block conversation
        if should_enable_duo(domain) and primary.lower() != "chip":
            scene_state["segment_type"] = "conversation"
            conv_text = write_block_conversation(
                primary     = primary,
                headline    = headline,
                synthesis   = summary,
                scene_state = scene_state,
                episode_id  = "episode",
                secondary   = secondary
            )
            lines = [ln for ln in conv_text.splitlines() if ":" in ln]
            first_line_chip = False
            for i, line in enumerate(lines):
                speaker_part, text_part = line.split(":", 1)
                speaker = speaker_part.strip().lower()
                text = text_part.strip().strip('"')
                tag = "chip_transition" if i == 0 and speaker == "chip" else (
                      "anchor_analysis" if i == 0 else
                      "anchor_analysis" if i == 1 and first_line_chip else
                      "duo_exchange")
                if i == 0 and speaker == "chip":
                    first_line_chip = True
                timeline.append(_block(text, speaker, tag))
                audio.append(_audio_block(text, speaker, tag, voice_map))
                scene_state["previous_line"] = {"speaker": speaker, "text": text}
                scene_state["block_index"] += 1

        # === Fallback: primary analysis only
        else:
            scene_state["segment_type"] = "analysis"
            solo_text = write_block_conversation(
                primary     = primary,
                headline    = headline,
                synthesis   = summary,
                scene_state = scene_state,
                episode_id  = "episode",
                secondary   = None
            )
            lines = [ln for ln in solo_text.splitlines() if ":" in ln]
            for i, line in enumerate(lines):
                speaker_part, text_part = line.split(":", 1)
                speaker = speaker_part.strip().lower()
                text = text_part.strip().strip('"')
                tag = "chip_transition" if i == 0 else "anchor_analysis"
                timeline.append(_block(text, speaker, tag))
                audio.append(_audio_block(text, speaker, tag, voice_map))
                scene_state["previous_line"] = {"speaker": speaker, "text": text}
                scene_state["block_index"] += 1

    # === CHIP OUTRO
    outro = "Thank you for watching ToknNews — we'll see you in the next block."
    timeline.append(_block(outro, "chip", "chip_outro"))
    audio.append(_audio_block(outro, "chip", "chip_outro", voice_map))
    scene_state["previous_line"] = {"speaker": "chip", "text": outro}
    scene_state["block_index"] += 1

    return {
        "blocks": timeline,
        "audio_blocks": audio
    }
