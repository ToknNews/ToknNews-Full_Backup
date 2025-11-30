#!/usr/bin/env python3
"""
pacing_engine.py
TOKEN NEWS — Episode Pacing Engine

This module builds a pacing plan (blueprint) for an episode:
- Determines number of stories
- Determines how many analysis / crosstalk blocks
- Injects bumpers (Vega + Chip)
- Ensures total runtime meets target duration (± tolerance)
- Never rushes speech or shortens blocks — only adds/removes blocks naturally
"""

from runtime.runtime_estimator import (
    estimate_block_duration,
    estimate_episode_duration
)


# =====================================================================
# CONFIG
# =====================================================================

TARGET_RUNTIME_SEC = 1200      # 20 minutes
RUNTIME_TOLERANCE_SEC = 90     # 18.5–21.5 min acceptable


MIN_STORIES = 4
MAX_STORIES = 12

# Estimated number of blocks per story (Chip toss + analysis + optional duo + transition)
AVG_BLOCKS_PER_STORY = 3.5

# Optional bumpers
VEGA_BUMPER_COST_SEC = 6.0
CHIP_RESET_COST_SEC = 5.0


# =====================================================================
# BUILD INITIAL PACING PLAN
# =====================================================================

def initial_story_count() -> int:
    """
    Returns a rough initial estimate of how many stories to include.
    This is refined later by runtime_goal_controller.
    """
    # Simple heuristic: assume each story cluster takes ~45–75 seconds
    avg_story_time = 60
    return max(MIN_STORIES, min(MAX_STORIES, TARGET_RUNTIME_SEC // avg_story_time))


# =====================================================================
# ESTIMATE STORY CLUSTER RUNTIME
# =====================================================================

def estimate_story_cluster_runtime(cluster) -> float:
    """
    cluster = {
       "headline": "...",
       "summary": "...",
       "anchors": ["reef", "bond"]
    }
    """
    headline = cluster.get("headline", "")
    summary  = cluster.get("summary", "")
    anchors  = cluster.get("anchors", [])

    total = 0.0

    # Chip toss
    total += estimate_block_duration("chip", f"Tossing to {anchors[0]} about {headline}.")

    # Primary analysis
    total += estimate_block_duration(anchors[0], summary)

    # Optional duo anchor
    if len(anchors) > 1:
        duo = anchors[1]
        total += estimate_block_duration(duo, f"Follow-up commentary on: {headline}")

    # Transition
    total += estimate_block_duration("chip", f"Transitioning from {headline}")

    return total


# =====================================================================
# PREPARE PACING BLUEPRINT
# =====================================================================

def build_pacing_blueprint(story_clusters: list) -> dict:
    """
    Build pacing blueprint BEFORE timeline_builder runs.
    story_clusters = list of story dicts from episode_builder.

    Output:
    {
        "target_runtime": 1200,
        "tolerance": 90,
        "stories_selected": [...],
        "expected_runtime": seconds,
        "vega_bumpers": int,
        "chip_resets": int,
        "notes": "..."
    }
    """

    pacing = {
        "target_runtime": TARGET_RUNTIME_SEC,
        "tolerance": RUNTIME_TOLERANCE_SEC,
        "stories_selected": [],
        "expected_runtime": 0.0,
        "vega_bumpers": 0,
        "chip_resets": 0,
        "notes": ""
    }

    # 1. Pick initial story_count based on heuristic
    story_count = initial_story_count()

    # Limit to available stories
    story_count = min(story_count, len(story_clusters))

    # Select the stories (already ranked by episode_builder)
    selected = story_clusters[:story_count]

    pacing["stories_selected"] = selected

    # 2. Estimate total runtime of these stories
    total_story_time = 0.0

    for cluster in selected:
        total_story_time += estimate_story_cluster_runtime(cluster)

    # 3. Add bumpers for pacing
    # One Vega bumper per 3 stories (rough heuristic)
    vega_bumpers = max(1, story_count // 3)
    chip_resets  = max(1, story_count // 4)

    total_bumper_time = vega_bumpers * VEGA_BUMPER_COST_SEC + chip_resets * CHIP_RESET_COST_SEC

    pacing["vega_bumpers"] = vega_bumpers
    pacing["chip_resets"] = chip_resets

    pacing["expected_runtime"] = total_story_time + total_bumper_time

    # 4. Add notes
    pacing["notes"] = (
        f"Initial pacing estimate: {story_count} stories, "
        f"{vega_bumpers} Vega bumpers, {chip_resets} Chip resets. "
        f"Estimated runtime ≈ {int(pacing['expected_runtime'])} sec."
    )

    return pacing


# =====================================================================
# TEST
# =====================================================================

if __name__ == "__main__":
    fake_clusters = [
        {"headline": "SEC investigates crypto exchange", "summary": "Regulators probing unusual flows.", "anchors": ["lawson"]},
        {"headline": "Ethereum staking rising", "summary": "Validators increase deposits.", "anchors": ["reef"]},
        {"headline": "AI chips surge", "summary": "GPU demand driving tech sector.", "anchors": ["neura"]}
    ]

    result = build_pacing_blueprint(fake_clusters)
    print(result)
