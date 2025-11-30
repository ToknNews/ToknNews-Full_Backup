#!/usr/bin/env python3
"""
TOKNNews — Timeline Builder (PD-Integrated Build, Revised Intro Logic)
Module C-8
"""
import random
import time

# Patch imports (Chip follow-up + RKG)
from script_engine.rolling_brain import get_brain_snapshot
from script_engine.openai_writer import gpt_analysis, gpt_reaction, gpt_duo_line, persona_prompt, _gpt

# ------------------------------------------------------------
# Imports (Package Mode; tests run via `python -m script_engine.run_test`)
# ------------------------------------------------------------
from script_engine.persona.line_builder import (
    apply_tone_shift,
    build_analysis_line,
    build_transition_line,
    build_vega_line,
    build_bitsy_interrupt,
    build_reaction_line,
    build_anchor_react
)
from script_engine.character_brain.persona_loader import get_voice, get_domain

# ------------------------------------------------------------
# Global writer toggle import (Package vs Local)
# ------------------------------------------------------------
try:
    from script_engine.engine_settings import USE_OPENAI_WRITER
except ImportError:
    from engine_settings import USE_OPENAI_WRITER

# ------------------------------------------------------------
# Primary Anchor Selection (Chip delegates based on domain)
# ------------------------------------------------------------
def select_primary_anchor(headline: str, brain: dict):
    """
    Choose the best anchor for this headline (domain + memory weight).
    """
    headline_l = headline.lower()
    # Simple domain detection
    if any(x in headline_l for x in ["eth", "ethereum", "rollup", "l2", "altcoin"]):
        domain = "altcoin"
    elif any(x in headline_l for x in ["btc", "bitcoin", "halving", "mining"]):
        domain = "bitcoin"
    elif any(x in headline_l for x in ["defi", "liquidity", "protocol", "amm", "yield"]):
        domain = "defi"
    elif any(x in headline_l for x in ["hacker", "exploit", "bridge", "hack", "drain"]):
        domain = "security"
    else:
        domain = "general"
    # Score anchors by domain match + brain memory weight
    scores = {}
    for anchor, data in brain["anchors"].items():
        specialty = data.get("domain", [])
        score = 0
        if domain in specialty:
            score += 10   # direct specialty alignment
        score += data.get("weight", 0)  # rolling memory weight
        scores[anchor] = score
    primary = max(scores, key=scores.get)
    primary_domain = domain
    return primary, primary_domain

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
        "text": text,
        "content": text,
        "timestamp": time.time()
    }

# ---------------------------------------------------------
# Intro Helpers — Vega Ident & Chip Opening (Static fallback)
# ---------------------------------------------------------
def _vega_ident_line():
    """Static fallback for Vega’s intro (used only if GPT unavailable)."""
    return "Good morning, and welcome to TOKN News."

def _chip_opening_line():
    """Static fallback for Chip’s greeting (used only if GPT unavailable)."""
    hour = time.localtime().tm_hour
    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"
    return f"{greeting}, I’m Chip. Let’s get straight into today’s top story."

# ============================================================
# Main — Build timeline based on PD instructions (Step 3-G)
# ============================================================
def build_timeline(
    headline: str,
    synthesis: str = "",
    article_context: str = "",
    cluster_articles=None,
    anchors=None,
    allow_bitsy=False,
    allow_vega=False,
    show_intro=False,
    segment_type="headline",
    tone_shift=None
):
    timeline = []
    audio_blocks = []

    # Snapshot the rolling brain state for context
    brain = get_brain_snapshot()

    # 1. Select primary anchor (Chip decides who leads this story)
    primary_anchor, primary_domain = select_primary_anchor(headline, brain)
    duo_anchor = None  # PD may assign a secondary anchor (duo) based on context
    speaker = primary_anchor  # primary speaker for this segment

    # --------------------------------------------------------
    # SHOW INTRO SEQUENCE — Vega ident (booth voice) + Chip greeting
    # --------------------------------------------------------
    if show_intro:
        # Vega opens the show
        vega_line = None
        chip_line = None
        if USE_OPENAI_WRITER:
            try:
                # Vega's GPT-generated welcome (one-liner, vibe only)
                persona_v = persona_prompt("vega", brain, mode="news", allow_multi=False)
                vega_prompt = (
                    f"{persona_v.strip()}\n\n"
                    "You are Vega Watt, the booth announcer. "
                    "In one sentence, warmly welcome the audience to TOKN News to kick off the show."
                )
                vega_line = _gpt(vega_prompt)
            except Exception as e:
                print("[TimelineBuilder] Vega intro generation error:", e)
                vega_line = None
            try:
                # Chip's GPT-generated greeting and rundown (2-3 sentences)
                tm = time.localtime()
                hour = tm.tm_hour
                if 5 <= hour < 12:
                    part_of_day = "morning"
                elif 12 <= hour < 18:
                    part_of_day = "afternoon"
                else:
                    part_of_day = "evening"
                day_name = time.strftime("%A", tm)
                date_str = time.strftime("%B %d, %Y", tm)
                # Basic holiday awareness (extendable)
                holiday = None
                if tm.tm_mon == 1 and tm.tm_mday == 1:
                    holiday = "New Year's Day"
                elif tm.tm_mon == 7 and tm.tm_mday == 4:
                    holiday = "Independence Day"
                elif tm.tm_mon == 10 and tm.tm_mday == 31:
                    holiday = "Halloween"
                elif tm.tm_mon == 12 and tm.tm_mday == 25:
                    holiday = "Christmas"
                elif tm.tm_mon == 11 and tm.tm_wday == 3 and 22 <= tm.tm_mday <= 28:
                    holiday = "Thanksgiving"
                persona_c = persona_prompt("chip", brain, mode="news", allow_multi=True)
                chip_prompt = (
                    f"{persona_c.strip()}\n\n"
                    f"You are Chip, the host. It's {part_of_day} on {day_name}, {date_str}."
                )
                if holiday:
                    chip_prompt += f" Today is {holiday},"
                chip_prompt += (
                    " welcome the audience and introduce the top stories of the day.\n"
                    f"Main Headline: \"{headline}\"\n"
                )
                if cluster_articles:
                    chip_prompt += "Other Top Headlines:\n"
                    for h in cluster_articles:
                        chip_prompt += f"- {h}\n"
                chip_prompt += (
                    "\nGuidelines:\n"
                    "- Start with a friendly greeting (reflect time of day"
                    + (", and mention the holiday)" if holiday else ")")
                    + ".\n- Transition into the main headline and briefly tease upcoming stories.\n"
                    "- Keep it concise (max 3 sentences) and engaging."
                )
                chip_line = _gpt(chip_prompt)
            except Exception as e:
                print("[TimelineBuilder] Chip greeting generation error:", e)
                chip_line = None

        # Fallback to static lines if GPT was not used or failed
        if not vega_line:
            vega_line = _vega_ident_line()
        if not chip_line:
            chip_line = _chip_opening_line()

        # Append Vega ident first (booth voice over intro music)
        timeline.append({
            "type": "vega_ident",
            "speaker": "vega",
            "text": vega_line,
            "tone_shift": None
        })
        # Append Chip’s greeting + rundown second (on-camera lead anchor)
        timeline.append({
            "type": "chip_open",
            "speaker": "chip",
            "text": chip_line,
            "tone_shift": tone_shift
        })

        # If Chip is **not** the primary anchor for the story, have Chip toss to the anchor
        if primary_anchor != "chip":
            toss_line = None
            if USE_OPENAI_WRITER:
                from script_engine.openai_writer import gpt_chip_toss
                try:
                    toss_line = gpt_chip_toss(
                        next_anchor=primary_anchor,
                        headline=headline,
                        brain=brain,
                        show_mode="news",
                        pd_flags={}
                    )
                except Exception as e:
                    print("[TimelineBuilder] Chip toss generation error:", e)
                    toss_line = None
            if toss_line:
                timeline.append({
                    "type": "chip_toss",
                    "speaker": "chip",
                    "text": toss_line,
                    "tone_shift": tone_shift
                })
    else:
        # No show intro (mid-show segment) — Chip directly tosses to the primary anchor if needed
        if primary_anchor != "chip":
            toss_line = None
            if USE_OPENAI_WRITER:
                from script_engine.openai_writer import gpt_chip_toss
                try:
                    toss_line = gpt_chip_toss(
                        next_anchor=primary_anchor,
                        headline=headline,
                        brain=brain,
                        show_mode="news",
                        pd_flags={}
                    )
                except Exception as e:
                    print("[TimelineBuilder] Chip toss generation error:", e)
                    toss_line = None
            if toss_line:
                timeline.append({
                    "type": "chip_toss",
                    "speaker": "chip",
                    "text": toss_line,
                    "tone_shift": tone_shift
                })
        else:
            # If Chip is the primary anchor and there's no intro, he can start with a quick remark on the headline
            if USE_OPENAI_WRITER:
                try:
                    chip_remark = gpt_reaction("chip", headline, brain)
                except Exception as e:
                    chip_remark = None
                    print("[TimelineBuilder] Chip self-intro remark error:", e)
            else:
                chip_remark = None
            if chip_remark:
                timeline.append({
                    "type": "chip_open",
                    "speaker": "chip",
                    "text": chip_remark,
                    "tone_shift": tone_shift
                })

    # --------------------------------------------------------
    # Primary Anchor's Reaction Line
    # --------------------------------------------------------
    reaction_text = build_reaction_line(speaker, headline, tone_shift=tone_shift)
    timeline.append({
        "type": "reaction",
        "speaker": speaker,
        "text": reaction_text,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # Primary Anchor's Analysis Line
    # --------------------------------------------------------
    analysis_text = build_analysis_line(speaker, headline, synthesis, article_context, tone_shift=tone_shift)
    timeline.append({
        "type": "analysis",
        "speaker": speaker,
        "text": analysis_text,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # Transition Line (anchors)
    # --------------------------------------------------------
    transition_text = build_transition_line(speaker, target_group="anchor", tone_shift=tone_shift)
    timeline.append({
        "type": "transition",
        "speaker": speaker,
        "text": transition_text,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # Quick React (primary anchor follow-up)
    # --------------------------------------------------------
    react_text = build_anchor_react(speaker, headline, tone_shift=tone_shift)
    timeline.append({
        "type": "quick_react",
        "speaker": speaker,
        "text": react_text,
        "tone_shift": tone_shift
    })

    # ------------------------------------------------------------
    # Duo Logic — Round 1 (if a secondary anchor is present)
    # ------------------------------------------------------------
    if duo_anchor:
        last_solo_speaker = timeline[-1]["speaker"] if timeline else None
        duo_blocks = _build_duo_crosstalk(
            primary_anchor,
            duo_anchor,
            headline,
            synthesis,
            tone_shift,
            last_solo_speaker
        )
        timeline.extend(duo_blocks)

    # ============================================================
    # Chip Follow-Up (Patch 7) — Chip reacts after anchors finish
    # ============================================================
    if primary_anchor != "chip":
        from script_engine.openai_writer import gpt_chip_followup, gpt_chip_toss
        chip_domain = get_domain("chip")
        chip_follow = None
        try:
            chip_follow = gpt_chip_followup(
                headline=headline,
                synthesis=synthesis,
                primary=primary_anchor,
                duo=duo_anchor,
                last_line=timeline[-1]["text"] if timeline else "",
                pd_flags={},
                show_mode="news",
                brain=brain,
                chip_domain=chip_domain
            )
        except Exception as e:
            print("[TimelineBuilder] Chip follow-up error:", e)
            chip_follow = None
        if chip_follow:
            timeline.append({
                "type": "chip_followup",
                "speaker": "chip",
                "text": chip_follow,
                "tone_shift": tone_shift
            })
            # Chip smart-toss to next anchor (determine who speaks next)
            next_anchor = primary_anchor  # default to primary anchor (no PD flags used here for brevity)
            toss_line = None
            try:
                toss_line = gpt_chip_toss(
                    next_anchor=next_anchor,
                    headline=headline,
                    brain=brain,
                    show_mode="news",
                    pd_flags={}
                )
            except Exception as e:
                toss_line = None
                print("[TimelineBuilder] Next-segment toss error:", e)
            if toss_line:
                timeline.append({
                    "type": "chip_toss",
                    "speaker": "chip",
                    "text": toss_line,
                    "tone_shift": tone_shift
                })
            # Removed the placeholder segment_reset line to avoid static script text
            # (Next anchor will continue in the following segment without a spoken cue)

    # (Patch 3+ additional follow-up question, round2 duo, Bitsy/Vega cameos, montage insertion omitted for brevity)

    # Return timeline and audio_blocks (audio will be rendered separately)
    return {
        "timeline": timeline,
        "audio_blocks": audio_blocks,
        "unreal": {}
    }
