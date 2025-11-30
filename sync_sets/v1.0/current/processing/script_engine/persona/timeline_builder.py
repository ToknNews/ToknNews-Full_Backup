#!/usr/bin/env python3
"""
TOKNNews — Timeline Builder (Full Rebuild, Clean Stack)
Module C-8
"""

import random
import time

# ============================================================
# Dual-Mode Imports (Package vs Local)
# ============================================================
try:
    from script_engine.persona.line_builder import (
        apply_tone_shift,
        build_analysis_line,
        build_transition_line,
        build_vega_line,
        build_bitsy_interrupt,
        build_reaction_line,
        build_anchor_react
    )
    from script_engine.character_brain.persona_loader import (
        get_voice,
        get_domain
    )
    from script_engine.engine_settings import USE_OPENAI_WRITER

except ImportError:
    from persona.line_builder import (
        apply_tone_shift,
        build_analysis_line,
        build_transition_line,
        build_vega_line,
        build_bitsy_interrupt,
        build_reaction_line,
        build_anchor_react
    )
    from character_brain.persona_loader import (
        get_voice,
        get_domain
    )
    from engine_settings import USE_OPENAI_WRITER

# ============================================================
# Brain Snapshot Import
# ============================================================
try:
    from script_engine.rolling_brain import get_brain_snapshot
except ImportError:
    from rolling_brain import get_brain_snapshot


# ============================================================
# Utility Blocks
# ============================================================
def _block(text, character, block_type):
    return {
        "type": block_type,
        "character": character,
        "voice_id": get_voice(character),
        "text": text,
        "timestamp": time.time(),
    }


def _audio_block(text, character, block_type):
    return {
        "character": character,
        "voice_id": get_voice(character),
        "block_type": block_type,
        "text": text,
        "content": text,
        "timestamp": time.time(),
    }

# ============================================================
# Intro Helper Lines — Vega Ident + Chip Opening
# ============================================================
def _vega_ident_line():
    """
    Vega is zero analysis, all vibe.
    This line should remain static for render reuse.
    """
    return "Welcome to Token News."


def _chip_opening_line():
    """
    Chip greets the audience with time-aware phrasing.
    """
    hour = time.localtime().tm_hour

    if 5 <= hour < 12:
        greeting = "Good morning"
    elif 12 <= hour < 18:
        greeting = "Good afternoon"
    else:
        greeting = "Good evening"

    return f"{greeting}, I’m Chip Blue and welcome to Token News. Let’s get straight into today’s top story."

def _chip_transition_line():
    """
    Chip transitions between stories after a Vega quip or a heavy segment.
    Short, reusable, and neutral.
    """
    return "Alright, let’s get back to it — here’s what’s next."

# ============================================================
# Primary Anchor Selection (Domain-based + Brain Weights)
# ============================================================
def select_primary_anchor(headline: str, brain: dict):
    """
    Returns (primary_anchor, primary_domain)
    Uses simple keyword→domain detection + rolling brain weights.
    """

    headline_l = headline.lower()

    # --- Basic domain inference ---
    if any(k in headline_l for k in ["ethereum", "eth", "rollup", "l2"]):
        domain = "altcoin"
    elif any(k in headline_l for k in ["btc", "bitcoin", "halving", "mining"]):
        domain = "bitcoin"
    elif any(k in headline_l for k in ["defi", "liquidity", "amm", "yield"]):
        domain = "defi"
    elif any(k in headline_l for k in ["exploit", "hacker", "hack", "bridge", "drain"]):
        domain = "security"
    else:
        domain = "general"

    # --- Score anchors ---
    scores = {}
    for anchor, data in brain["anchors"].items():
        specialties = data.get("domain", [])
        weight = data.get("weight", 0)

        score = weight
        if domain in specialties:
            score += 10

        scores[anchor] = score

    primary = max(scores, key=scores.get)
    return primary, domain


# ============================================================
# CHIP — Smart Toss System
# ============================================================
def chip_toss_line(next_anchor: str, mode: str = "news"):
    """
    Chip toss phrases.
    mode = "news" | "latenight"
    """

    if mode == "latenight":
        lines = {
            "reef":   "Reef, what’s the late-night pulse on this?",
            "lawson": "Lawson, break down the macro angle for us.",
            "ledger": "Ledger, walk us through the flows here.",
            "penny":  "Penny, what’s the retail read tonight?",
            "rex":    "Rex, volatility check — what are you seeing?",
            "bitsy":  "Bitsy, give us the sentiment read on this.",
            "vega":   "Vega, cool us down — what’s the vibe?",
        }
    else:
        lines = {
            "reef":   "Reef, what’s the DeFi angle here?",
            "lawson": "Lawson, give us the macro frame.",
            "ledger": "Ledger, what’s happening on-chain?",
            "penny":  "Penny, how’s retail reacting?",
            "rex":    "Rex, where’s the volatility pressure?",
            "bitsy":  "Bitsy, what’s sentiment telling us?",
            "vega":   "Vega, reset the tone for us.",
        }

    return lines.get(next_anchor, f"{next_anchor}, what’s your read?")

# ============================================================
# DUO CROSSTALK ENGINE (GPT-driven, persona-aware)
# ============================================================
def _build_duo_crosstalk(
    primary: str,
    duo: str,
    headline: str,
    synthesis: str,
    tone_shift: str,
    last_solo_speaker: str,
    show_mode: str = "news",
    brain: dict = None
):
    """
    Produces a natural back-and-forth between two anchors using GPT.
    Includes:
        • Turn-taking
        • Contextual referencing
        • Persona divergence
        • Noun diversity enforcement
        • Show-mode adaptation (news vs latenight)
    """

    from script_engine.openai_writer import gpt_duo_line
    from script_engine.character_brain.persona_loader import get_domain

    if brain is None:
        brain = get_brain_snapshot()

    # Domains for deeper GPT prompting
    primary_domain = get_domain(primary)
    duo_domain     = get_domain(duo)

    # If the last solo speaker was the primary, swap roles
    if last_solo_speaker == primary:
        primary, duo = duo, primary
        primary_domain, duo_domain = duo_domain, primary_domain

    blocks = []
    used_terms = set()
    last_line = None

    # --------------------------------------------
    # Anti-loop filter for repeated nouns
    # --------------------------------------------
    def filter_repeated_terms(text):
        nonlocal used_terms
        if not text:
            return None

        terms = [
            "liquidity", "flow", "imbalance", "whale",
            "protocol", "cluster", "yield", "volatility",
            "pressure", "anomaly"
        ]

        for t in terms:
            if t in used_terms and t in text.lower():
                return None

        for t in terms:
            if t in text.lower():
                used_terms.add(t)

        return text

    # --------------------------------------------
    # DUO SEQUENCE (React → Counter → Analysis → Counter → Transition → Transition → Close)
    # --------------------------------------------

    # 1. Primary react
    p_react = gpt_duo_line(
        speaker=primary,
        counter=duo,
        headline=headline,
        synthesis=synthesis,
        domain=primary_domain,
        duo_mode="react",
        last_counter_line=last_line,
        show_mode=show_mode,
        brain=brain
    )
    p_react = filter_repeated_terms(p_react)
    if p_react:
        blocks.append({
            "type": "duo_primary_react",
            "speaker": primary,
            "text": p_react,
            "tone_shift": tone_shift
        })
        last_line = p_react

    # 2. Duo react
    d_react = gpt_duo_line(
        speaker=duo,
        counter=primary,
        headline=headline,
        synthesis=synthesis,
        domain=duo_domain,
        duo_mode="react",
        last_counter_line=last_line,
        show_mode=show_mode,
        brain=brain
    )
    d_react = filter_repeated_terms(d_react)
    if d_react:
        blocks.append({
            "type": "duo_secondary_react",
            "speaker": duo,
            "text": d_react,
            "tone_shift": tone_shift
        })
        last_line = d_react

    # 3. Primary analysis
    p_anal = gpt_duo_line(
        speaker=primary,
        counter=duo,
        headline=headline,
        synthesis=synthesis,
        domain=primary_domain,
        duo_mode="analysis",
        last_counter_line=last_line,
        show_mode=show_mode,
        brain=brain
    )
    p_anal = filter_repeated_terms(p_anal)
    if p_anal:
        blocks.append({
            "type": "duo_primary_analysis",
            "speaker": primary,
            "text": p_anal,
            "tone_shift": tone_shift
        })
        last_line = p_anal

    # 4. Duo counter-analysis
    d_anal = gpt_duo_line(
        speaker=duo,
        counter=primary,
        headline=headline,
        synthesis=synthesis,
        domain=duo_domain,
        duo_mode="analysis",
        last_counter_line=last_line,
        show_mode=show_mode,
        brain=brain
    )
    d_anal = filter_repeated_terms(d_anal)
    if d_anal:
        blocks.append({
            "type": "duo_secondary_analysis",
            "speaker": duo,
            "text": d_anal,
            "tone_shift": tone_shift
        })
        last_line = d_anal

    # 5. Primary transition
    p_trans = gpt_duo_line(
        speaker=primary,
        counter=duo,
        headline=headline,
        synthesis=synthesis,
        domain=primary_domain,
        duo_mode="transition",
        last_counter_line=last_line,
        show_mode=show_mode,
        brain=brain
    )
    p_trans = filter_repeated_terms(p_trans)
    if p_trans:
        blocks.append({
            "type": "duo_primary_transition",
            "speaker": primary,
            "text": p_trans,
            "tone_shift": tone_shift
        })
        last_line = p_trans

    # 6. Duo transition
    d_trans = gpt_duo_line(
        speaker=duo,
        counter=primary,
        headline=headline,
        synthesis=synthesis,
        domain=duo_domain,
        duo_mode="transition",
        last_counter_line=last_line,
        show_mode=show_mode,
        brain=brain
    )
    d_trans = filter_repeated_terms(d_trans)
    if d_trans:
        blocks.append({
            "type": "duo_secondary_transition",
            "speaker": duo,
            "text": d_trans,
            "tone_shift": tone_shift
        })
        last_line = d_trans

    # 7. Primary close
    p_close = gpt_duo_line(
        speaker=primary,
        counter=duo,
        headline=headline,
        synthesis=synthesis,
        domain=primary_domain,
        duo_mode="close",
        last_counter_line=last_line,
        show_mode=show_mode,
        brain=brain
    )
    p_close = filter_repeated_terms(p_close)
    if p_close:
        blocks.append({
            "type": "duo_primary_close",
            "speaker": primary,
            "text": p_close,
            "tone_shift": tone_shift
        })

    return blocks

# ============================================================
# PD SCORING ENGINE (sentiment, volatility, contradiction)
# ============================================================
def pd_score_segment(headline: str, brain: dict, duo_round1: list):
    """
    Computes PD flags for:
        • volatility
        • sentiment impact
        • contradiction detection
        • tragedy guardrails
        • latenight qualifiers
    """

    text = headline.lower() + " " + str(brain).lower()

    pd = {
        "tragic": False,
        "contradiction": 0,
        "social_heat": 0.0,
        "volatility_risk": 0.0,
        "latenight_mode": False,
    }

    # --- Tragedy check ---
    tragic_terms = ["dead", "death", "killed", "shooting", "collapse", "terror", "tragedy"]
    if any(t in text for t in tragic_terms):
        pd["tragic"] = True

    # --- Contradiction detection from duo ---
    if len(duo_round1) >= 2:
        last1 = duo_round1[-1]["text"].lower()
        last2 = duo_round1[-2]["text"].lower()
        contras = ["but", "however", "not exactly", "disagree"]
        if any(c in last1 for c in contras) or any(c in last2 for c in contras):
            pd["contradiction"] = 1

    # --- Social heat (simplified placeholder) ---
    try:
        heat = brain.get("sentiment", {}).get("global", 0.3)
        pd["social_heat"] = float(heat)
    except:
        pd["social_heat"] = 0.3

    # --- Volatility indicator ---
    if "volatility" in text or "liquidation" in text or "whale" in text:
        pd["volatility_risk"] = 0.6

    # --- Latenight Mode (placeholder simplified logic) ---
    hour = time.localtime().tm_hour
    if (21 <= hour <= 23) or (0 <= hour <= 2):
        pd["latenight_mode"] = True

    return pd


# ============================================================
# SHOW MODE RESOLVER (news vs latenight)
# ============================================================
def resolve_show_mode(pd_flags: dict):
    """
    LateNight applies only if:
        • not tragic
        • PD late-night toggle is True
    """
    if pd_flags["tragic"]:
        return "news"
    if pd_flags["latenight_mode"]:
        return "latenight"
    return "news"


# ============================================================
# Bitsy + Vega cameo rules (tone safe)
# ============================================================
def bitsy_allowed(pd_flags: dict):
    """ Bitsy never appears during tragedy. """
    return not pd_flags["tragic"]


def vega_allowed(pd_flags: dict):
    """ Vega also hides during tragedy. """
    return not pd_flags["tragic"]

# ============================================================
# GPT CHIP FOLLOW-UP ENGINE
# ============================================================
def chip_followup_gpt(
    primary_anchor: str,
    duo_anchor: str,
    headline: str,
    synthesis: str,
    last_line: str,
    show_mode: str,
    pd_flags: dict,
    brain: dict
):
    """
    Chip asks a clarifying follow-up question using GPT.
    Strong personality. Short. Mode-aware.
    """

    from script_engine.openai_writer import gpt_chip_followup

    # fallback if GPT is disabled
    if not USE_OPENAI_WRITER:
        return f"{primary_anchor}, before we wrap, what's the key signal to watch?"

    return gpt_chip_followup(
        primary=primary_anchor,
        duo=duo_anchor,
        headline=headline,
        last_line=last_line,
        show_mode=show_mode,
        pd_flags=pd_flags,
        brain=brain
    )


# ============================================================
# GPT CHIP SMART TOSS
# ============================================================
def chip_smart_toss_gpt(
    next_anchor: str,
    headline: str,
    show_mode: str,
    pd_flags: dict,
    brain: dict
):
    """
    Chip's GPT-driven rhetorical toss into the next speaker.
    """
    from script_engine.openai_writer import gpt_chip_toss

    if not USE_OPENAI_WRITER:
        return f"{next_anchor}, continue the breakdown for us."

    return gpt_chip_toss(
        next_anchor=next_anchor,
        headline=headline,
        show_mode=show_mode,
        pd_flags=pd_flags,
        brain=brain
    )

# ============================================================
# MAIN — build_timeline()
# ============================================================
def build_timeline(
    headline: str,
    synthesis: str = "",
    article_context: str = "",
    anchors=None,
    allow_bitsy=True,
    allow_vega=True,
    show_intro=True,
    segment_type="headline",
    tone_shift=None
):
    # Determine show mode for all downstream logic
    mode = "latenight" if segment_type == "latenight" else "news"

    timeline = []
    audio_blocks = []

    # --------------------------------------------------------
    # Brain + Primary Anchor Assignment
    # --------------------------------------------------------
    brain = get_brain_snapshot()

    if anchors is None:
        primary_anchor, primary_domain = select_primary_anchor(headline, brain)
        duo_anchor = None
    else:
        primary_anchor = anchors[0]
        duo_anchor = anchors[1] if len(anchors) > 1 else None
        primary_domain = get_domain(primary_anchor)

    speaker = primary_anchor

    # --------------------------------------------------------
    # SHOW INTRO (Vega Ident + Chip Opening)
    # --------------------------------------------------------
    if show_intro and segment_type == "headline":
        vega_ident = _vega_ident_line()
        timeline.append({
            "type": "vega_ident",
            "speaker": "vega",
            "text": vega_ident,
            "tone_shift": None
        })

        chip_open = _chip_opening_line()
        timeline.append({
            "type": "chip_open",
            "speaker": "chip",
            "text": chip_open,
            "tone_shift": None
        })
    # --------------------------------------------------------
    # GPT STORY INTRO — Chip frames the FIRST headline
    # --------------------------------------------------------
    try:
        from script_engine.openai_writer import gpt_chip_story_intro
    except ImportError:
        from openai_writer import gpt_chip_story_intro

    chip_story_intro = gpt_chip_story_intro(
        headline=headline,
        synthesis=synthesis,
        brain=brain,
        show_mode=mode
    )

    if chip_story_intro:
        timeline.append({
            "type": "chip_story_intro",
            "speaker": "chip",
            "text": chip_story_intro,
            "tone_shift": tone_shift
        })


    # --------------------------------------------------------
    # PD Scoring + Show Mode
    # --------------------------------------------------------
    pd_flags = {
        "tragic": False,
        "contradiction": 0,
        "social_heat": 0.3,
        "volatility_risk": 0.0,
        "latenight_mode": False,
    }
    show_mode = "news"   # placeholder, updated after duo

    # --------------------------------------------------------
    # CHIP TOSS — Chip introduces the anchor
    # --------------------------------------------------------
    toss_line = chip_toss_line(primary_anchor, mode=show_mode)
    timeline.append({
        "type": "chip_toss",
        "speaker": "chip",
        "text": toss_line,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # REACTION — primary anchor
    # --------------------------------------------------------
    reaction_text = build_reaction_line(
        speaker,
        headline,
        tone_shift=tone_shift
    )
    timeline.append({
        "type": "reaction",
        "speaker": speaker,
        "text": reaction_text,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # ANALYSIS — primary anchor
    # --------------------------------------------------------
    analysis_text = build_analysis_line(
        speaker,
        headline,
        synthesis,
        article_context,
        tone_shift=tone_shift
    )
    timeline.append({
        "type": "analysis",
        "speaker": speaker,
        "text": analysis_text,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # TRANSITION — primary anchor
    # --------------------------------------------------------
    transition_text = build_transition_line(
        speaker,
        headline,
        brain,
        target_group="anchor",
        tone_shift=tone_shift
    )

    timeline.append({
        "type": "transition",
        "speaker": speaker,
        "text": transition_text,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # QUICK REACT — primary anchor
    # --------------------------------------------------------
    quick_react_text = build_anchor_react(
        speaker,
        headline,
        brain,
        tone_shift=tone_shift
    )

    timeline.append({
        "type": "quick_react",
        "speaker": speaker,
        "text": quick_react_text,
        "tone_shift": tone_shift
    })

    # --------------------------------------------------------
    # DUO LOGIC — If duo anchor is provided
    # --------------------------------------------------------
    duo_round1 = []
    if duo_anchor:
        last_solo_speaker = timeline[-1]["speaker"]
        duo_round1 = _build_duo_crosstalk(
            primary_anchor,
            duo_anchor,
            headline,
            synthesis,
            tone_shift,
            last_solo_speaker,
            show_mode="news",
            brain=brain
        )
        timeline.extend(duo_round1)

        # Update PD flags + show mode based on duo
        pd_flags = pd_score_segment(headline, brain, duo_round1)
        show_mode = resolve_show_mode(pd_flags)

    # --------------------------------------------------------
    # CHIP FOLLOW-UP — GPT Question
    # --------------------------------------------------------
    if duo_anchor:
        last_line = timeline[-1]["text"]
        chip_follow = chip_followup_gpt(
            primary_anchor,
            duo_anchor,
            headline,
            synthesis,
            last_line,
            show_mode,
            pd_flags,
            brain
        )

        timeline.append({
            "type": "chip_followup",
            "speaker": "chip",
            "text": chip_follow,
            "tone_shift": tone_shift
        })

    # --------------------------------------------------------
    # Bitsy or Vega Cameo (Tone + PD driven) – Revised Logic
    # --------------------------------------------------------
    if pd_flags["bitsy_ok"] and allow_bitsy and random.random() < pd_flags["social_heat"]:
        # Chip explicitly tosses to Bitsy for a cultural/social sentiment take
        chip_bitsy_toss = build_transition_line("chip", target_group="bitsy", tone_shift=tone_shift)
        timeline.append({
            "type": "chip_toss",  # Chip cues Bitsy cameo
            "speaker": "chip",
            "text": chip_bitsy_toss,
            "tone_shift": tone_shift
        })
        # Bitsy responds with a GPT-generated interrupt line (humorous/meta commentary)
        bitsy_line = build_bitsy_interrupt("bitsy", headline, tone_shift)
        timeline.append({
            "type": "bitsy_interrupt",
            "speaker": "bitsy",
            "text": bitsy_line,
            "tone_shift": tone_shift
        })

    if pd_flags["vega_ok"] and allow_vega and pd_flags["volatility_risk"] > 0:
        # Chip summons Vega for a quick quip when news is heavy or needs a vibe boost
        chip_vega_toss = build_transition_line("chip", target_group="vega", tone_shift=tone_shift)
        timeline.append({
            "type": "chip_toss",  # Chip cues Vega cameo
            "speaker": "chip",
            "text": chip_vega_toss,
            "tone_shift": tone_shift
        })
        # Vega delivers a short GPT-generated reaction or pacing reset quip
        vega_line = build_vega_line("vega", headline, tone_shift)
        timeline.append({
            "type": "vega_pace_reset",
            "speaker": "vega",
            "text": vega_line,
            "tone_shift": tone_shift
        })

    # --------------------------------------------------------
    # RETURN PACKAGE — Clean Unreal metadata + audio blocks
    # --------------------------------------------------------
    scene_id = f"scene_{int(time.time())}"

    return {
        "timeline": timeline,
        "audio_blocks": audio_blocks,
        "unreal": {
            "scene_id": scene_id,
            "anchors": [primary_anchor] + ([duo_anchor] if duo_anchor else []),
            "primary_anchor": primary_anchor,
            "duo_anchor": duo_anchor
        }
    }

# ============================================================
# Local Test Runner (Optional)
# ============================================================
if __name__ == "__main__":
    sample = build_timeline(
        headline="Solana ETF surge continues",
        synthesis="capital rotation into Solana ecosystem",
        article_context="",
        anchors=["reef", "ledger"],
        allow_bitsy=True,
        allow_vega=True,
        show_intro=True,
        segment_type="headline",
        tone_shift=None
    )

    import json
    print(json.dumps(sample, indent=2))
