#!/usr/bin/env python3
import sys, os
sys.path.append("/var/www/toknnews-repo")

# ============================================================
# PACKAGE IMPORTS (Stable for python3 -m execution)
# ============================================================

from script_engine.character_brain.persona_loader import get_character_bible
from script_engine.persona.timeline_builder import build_timeline
from script_engine.synthesis_engine import build_synthesis
from script_engine.director.pd_controller import run_pd, select_anchors
from script_engine.engine_settings import USE_OPENAI_WRITER

import json
import time

# =====================================================================
#  MASTER ENTRYPOINT
# =====================================================================

def generate_script(
    headline: str,
    article_context: str = "",
    cluster_articles: list = None,
    anchors: list = None
):
    # Local import to ensure correct runtime path
    try:
        from script_engine.audio.audio_block_renderer import render_audio_blocks
    except ImportError:
        from audio.audio_block_renderer import render_audio_blocks

    # 1. Multi-article synthesis (basic for now)
    if cluster_articles:
        synthesis = headline
    else:
        synthesis = headline

    # 2. Build timeline using persona + tone engine
    package = build_timeline(
        headline=headline,
        synthesis=synthesis,
        article_context=article_context,
        anchors=anchors,
        allow_bitsy=True,
        allow_vega=True,
        show_intro=True,
        segment_type="headline",
        tone_shift=None
    )

    # 3. AUDIO
    scene_id = package["unreal"].get("scene_id") or f"scene_{int(time.time())}"
    final_audio = render_audio_blocks(scene_id, package["audio_blocks"])

    return {
        "timestamp": time.time(),
        "headline": headline,
        "synthesis": synthesis,
        "timeline": package["timeline"],
        "audio_blocks": package["audio_blocks"],
        "audio_file": final_audio,
        "unreal": package["unreal"]
    }

    # -----------------------------------------------------
    # 1. Multi-article synthesis
    # -----------------------------------------------------
    if cluster_articles:
        synthesis = build_synthesis(headline, cluster_articles)
    else:
        synthesis = build_synthesis(headline, [])

    # -----------------------------------------------------
    # 2. PD routing — determines segment type and rules
    # -----------------------------------------------------

    bible = get_character_bible()
    pd_config = run_pd(headline, bible)

    segment_type = pd_config["segment_type"]

    anchors = select_anchors(
        state=pd_config,
        headline=headline,
        personas=bible
    )
    primary_domain = pd_config.get("primary_domain")
    allow_bitsy = pd_config["allow_bitsy"]
    allow_vega = pd_config["allow_vega"]
    show_intro = pd_config["show_intro"]
    tone_shift = pd_config.get("tone_shift")

    # ------------------------------------------------------------
    # 3. Build timeline using persona + tone engine
    # ------------------------------------------------------------
    package = build_timeline(
        headline=headline,
        synthesis=synth,
        article_context=context,
        anchors=anchors,
        allow_bitsy=allow_bitsy,
        allow_vega=allow_vega,
        show_intro=show_intro,
        segment_type=segment_type,
        tone_shift=tone_shift
    )

    # === AUDIO (via tokn-audio service) ===

    scene_id = package["unreal"].get("scene_id") or f"scene_{int(time.time())}"

    final_audio = render_audio_blocks(scene_id, package["audio_blocks"])

    return {
        "timestamp": time.time(),
        "headline": headline,
        "synthesis": synth,
        "timeline": package["timeline"],
        "audio_blocks": package["audio_blocks"],
        "audio_file": final_audio,
        "unreal": package["unreal"]
    }

# =====================================================================
#  TEST MODE
# =====================================================================

if __name__ == "__main__":
    sample = generate_script(
        headline="Solana ETFs surge in early trading",
        article_context="Strong rotational flows into risk-on assets.",
        cluster_articles=[
            "ETH sees increased staker deposits",
            "BTC ETF inflows steady despite volatility"
        ],
        character="chip"
    )
    print(json.dumps(sample, indent=2))
