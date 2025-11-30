#!/usr/bin/env python3
"""
runtime_goal_controller.py
TOKEN NEWS — Runtime Goal Controller (20-minute episodes)

Works with:
 - runtime_estimator (pre- and post-audio predictions)
 - pacing_engine (initial pacing blueprint)
 - episode_builder (story clusters)
 - timeline_builder (final block construction)

Goal:
 - Adjust pacing until predicted episode runtime is within
   TARGET ± TOLERANCE
 - NEVER rush speech or compress audio
 - Only add/remove story clusters or bumpers
 - Prepare a "final episode layout" for episode_runner
"""

from runtime.runtime_estimator import (
    estimate_episode_duration,
    estimate_block_duration
)
from runtime.pacing_engine import (
    TARGET_RUNTIME_SEC,
    RUNTIME_TOLERANCE_SEC,
    build_pacing_blueprint,
    estimate_story_cluster_runtime,
    VEGA_BUMPER_COST_SEC,
    CHIP_RESET_COST_SEC
)


# =======================================================================
# Helpers
# =======================================================================

def within_tolerance(val: float, target: float, tol: float) -> bool:
    return abs(val - target) <= tol


def add_extra_bumper(blueprint: dict, type_: str):
    """Add Vega or Chip filler to inflate runtime safely."""
    if type_ == "vega":
        blueprint["vega_bumpers"] += 1
        blueprint["expected_runtime"] += VEGA_BUMPER_COST_SEC
    elif type_ == "chip":
        blueprint["chip_resets"] += 1
        blueprint["expected_runtime"] += CHIP_RESET_COST_SEC


def remove_last_story(blueprint: dict):
    """Remove the last story cluster to shrink runtime."""
    if blueprint["stories_selected"]:
        removed = blueprint["stories_selected"].pop()
        blueprint["expected_runtime"] -= estimate_story_cluster_runtime(removed)


def add_story_if_available(blueprint: dict, all_clusters: list):
    """Add next ranked story if exists."""
    used = len(blueprint["stories_selected"])
    if used < len(all_clusters):
        next_story = all_clusters[used]
        blueprint["stories_selected"].append(next_story)
        blueprint["expected_runtime"] += estimate_story_cluster_runtime(next_story)


# =======================================================================
# MAIN CONTROLLER
# =======================================================================

def reach_runtime_goal(all_story_clusters: list) -> dict:
    """
    Coordinates pacing adjustments until estimated runtime is within target.
    Returns a final blueprint ready for timeline_builder.
    """

    blueprint = build_pacing_blueprint(all_story_clusters)

    target = blueprint["target_runtime"]
    tol = blueprint["tolerance"]

    # Try up to 20 iterations (never infinite loop)
    for _ in range(20):

        est = blueprint["expected_runtime"]

        # 1. If within tolerance, we are finished
        if within_tolerance(est, target, tol):
            blueprint["notes"] += f" | Locked in runtime ~ {int(est)} sec."
            return blueprint

        # 2. If UNDER target — fill the runtime naturally
        if est < target:
            # First add a story if available and runtime is very low
            if len(blueprint["stories_selected"]) < 10 and target - est > 45:
                add_story_if_available(blueprint, all_story_clusters)
                continue

            # Otherwise add a bumper
            if target - est > 12:
                add_extra_bumper(blueprint, "vega")
                continue
            else:
                add_extra_bumper(blueprint, "chip")
                continue

        # 3. If OVER target — shrink runtime
        if est > target:
            # Remove last story if we have plenty
            if len(blueprint["stories_selected"]) > 4:
                remove_last_story(blueprint)
                continue

            # Otherwise reduce bumpers
            if blueprint["chip_resets"] > 1:
                blueprint["chip_resets"] -= 1
                blueprint["expected_runtime"] -= CHIP_RESET_COST_SEC
                continue

            if blueprint["vega_bumpers"] > 1:
                blueprint["vega_bumpers"] -= 1
                blueprint["expected_runtime"] -= VEGA_BUMPER_COST_SEC
                continue

    # If max attempts reached, return best attempt
    blueprint["notes"] += (
        " | WARNING: Max pacing iterations reached. "
        f"Final estimate ~ {int(blueprint['expected_runtime'])} sec."
    )
    return blueprint


# =======================================================================
# TEST
# =======================================================================

if __name__ == "__main__":
    fake_clusters = [
        {"headline": "SEC investigates exchange", "summary": "Probe launched.", "anchors": ["lawson"]},
        {"headline": "Liquidity jumps in DeFi", "summary": "TVL rising fast.", "anchors": ["reef"]},
        {"headline": "GPU shortages return", "summary": "AI compute pressure.", "anchors": ["neura"]},
        {"headline": "Consumers pull back", "summary": "Retail sentiment dips.", "anchors": ["penny"]},
        {"headline": "Market volatility spikes", "summary": "Night chaos underway.", "anchors": ["rex"]},
    ]

    result = reach_runtime_goal(fake_clusters)
    print(result)
