#!/usr/bin/env python3
import sys, os
sys.path.append("/var/www/toknnews-repo")

"""
TOKNNews — Script Engine V3 (Final PD-Integrated Build)
"""

import json
import time

# === Persona + Tone + Timeline Engines ===
from script_engine.persona.timeline_builder import build_timeline
from script_engine.synthesis_engine import build_synthesis

# === PD Orchestrator ===
from script_engine.director.pd_controller import run_pd

# =====================================================================
#  MASTER ENTRYPOINT
# =====================================================================

def generate_script(
        headline: str,
        article_context: str = "",
        cluster_articles: list = None,
        character: str = "chip"
    ):
    """
    Master entrypoint for Script Engine V3 + PD Integration.

    Returns:
      {
        timestamp,
        headline,
        character,
        synthesis,
        timeline[],
        audio_blocks[],
        unreal{}
      }
    """

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

    pd_config = run_pd(headline)

    segment_type = pd_config["segment_type"]
    anchors = pd_config["anchors"]
    allow_bitsy = pd_config["allow_bitsy"]
    allow_vega = pd_config["allow_vega"]
    show_intro = pd_config["show_intro"]
    tone_shift = pd_config.get("tone_shift")

    # -----------------------------------------------------
    # 3. Build timeline using persona + tone engine
    # -----------------------------------------------------
    package = build_timeline(
        character=character,
        headline=headline,
        synthesis=synthesis,
        article_context=article_context,
        anchors=anchors,
        allow_bitsy=allow_bitsy,
        allow_vega=allow_vega,
        show_intro=show_intro,
        segment_type=segment_type,
        tone_shift=tone_shift
    )

    # === AUDIO (via tokn-audio service) ===
    from script_engine.audio.audio_block_renderer import render_audio_blocks

    scene_id = package["unreal"].get("scene_id") or f"scene_{int(time.time())}"

    final_audio = render_audio_blocks(scene_id, package["audio_blocks"])

    return {
        "timestamp": time.time(),
        "headline": headline,
        "character": character,
        "synthesis": synthesis,
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
