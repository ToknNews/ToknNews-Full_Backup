#!/usr/bin/env python3
"""
scene_state.py
TOKEN NEWS — Scene State Engine

This module creates a structured "scene state" object for each block
generated during an episode. The state is passed to GPT so characters
have full awareness of:
 - who spoke before them
 - who speaks after
 - cast members in the scene
 - segment type (chip_rundown, anchor_analysis, duo, transition, bumper)
 - daypart (morning / afternoon / evening / latenight)
 - show_mode (NEWS / LATENIGHT / BREAKING)
 - PD flags

This also supports the upcoming Conversation Memory Engine (D).
"""

import time


# ======================================================================
# Scene State Constructor
# ======================================================================

def build_scene_state(
    current_anchor: str,
    previous_line: dict | None,
    next_anchor: str | None,
    cast_list: list,
    segment_type: str,
    show_mode: str,
    daypart: str,
    pd_flags: dict,
    episode_index: int,
    block_index: int
) -> dict:
    """
    Returns a standardized scene state dictionary.

    previous_line:
        {
          "speaker": "chip",
          "text": "Let's zoom out..."
        }

    next_anchor: "reef"

    cast_list: ["chip", "reef", "cash"]

    segment_type: e.g. "anchor_analysis", "chip_rundown", "vega_bumper"

    show_mode: "NEWS" | "LATENIGHT" | "BREAKING"

    daypart: "morning" | "afternoon" | "evening" | "latenight"

    pd_flags: {
       "is_breaking": False,
       "volatility_risk": 0.2,
       "social_heat": 0.1
    }

    episode_index: which story/segment we are in (0–N)
    block_index: sequential block number within the segment
    """

    state = {
        "timestamp": time.time(),

        "current_anchor": current_anchor.lower(),
        "previous_line": previous_line or None,
        "next_anchor": next_anchor.lower() if next_anchor else None,

        "cast_list": [c.lower() for c in cast_list],
        "segment_type": segment_type,
        "show_mode": show_mode,
        "daypart": daypart,

        "pd_flags": pd_flags or {
            "is_breaking": False,
            "volatility_risk": 0.0,
            "social_heat": 0.0
        },

        "episode_index": episode_index,
        "block_index": block_index,

        # GPT Quality Enhancers
        "gpt_context": {
            "awareness": (
                "You are aware of who spoke before you, who comes after, "
                "which anchors are in the scene, and which segment type "
                "you are currently in."
            ),
            "relationship_rules": (
                "Chip = rational narrator. Reef = fast DeFi take. "
                "Bond = heavy macro. Lawson = legal. Ivy = sentiment. "
                "Cash = retail psychology. Penny = human interest. "
                "Ledger = onchain data. Bitsy = chaos gremlin. "
                "Rex = night volatility. Vega = booth voiceover."
            ),
        }
    }

    return state


# ======================================================================
# Test
# ======================================================================

if __name__ == "__main__":
    example = build_scene_state(
        current_anchor="reef",
        previous_line={"speaker": "chip", "text": "Let's zoom out for a moment."},
        next_anchor="cash",
        cast_list=["chip", "reef", "cash"],
        segment_type="anchor_analysis",
        show_mode="NEWS",
        daypart="evening",
        pd_flags={"is_breaking": False, "volatility_risk": 0.1, "social_heat": 0.2},
        episode_index=2,
        block_index=0
    )

    print(example)
