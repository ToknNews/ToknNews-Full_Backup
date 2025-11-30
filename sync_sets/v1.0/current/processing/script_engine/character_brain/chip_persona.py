"""
Chip Persona Engine — Unified Hybrid Line Builder (A-5)
"""

import random
from script_engine.hybrid_tone.chip_tone_shaper import (
    compute_chip_tone_weight,
    apply_chip_tone_to_line,
)

# -----------------------------------------
# CHIP TONE TABLE (from A-2)
# -----------------------------------------
CHIP_TONE_TABLE = {
    "positive": [
        "Promising move here —",
        "Tailwinds showing —",
        "Looking solid —",
        "Momentum’s picking up —",
    ],
    "neutral": [
        "Alright —",
        "Let’s take a steady look —",
        "Here’s where things stand —",
        "Nothing wild yet —",
    ],
    "negative": [
        "Let’s stay sharp on this one —",
        "Not ideal here —",
        "This one’s concerning —",
        "We’ve seen this pattern before —",
    ],
    "breaking": [
        "Okay — developing news right now —",
        "Stay sharp — this is moving fast —",
        "Here’s what we know at this moment —",
        "Tracking this in real time —",
    ],
    "late_night": [
        "At this hour? Alright —",
        "Still awake? Let’s walk through it —",
        "Late-night update incoming —",
        "Okay — caffeine check —",
    ],
    "high_importance": [
        "This one actually matters —",
        "Let’s hit this properly —",
        "This is one of the big stories today —",
    ],
}

def choose_chip_starter(enriched):
    """Choose opening phrase based on sentiment & importance."""
    sentiment = enriched.get("sentiment", "neutral").lower()
    importance = enriched.get("importance", 5)
    hour = enriched.get("hour", 14)

    if importance >= 8:
        pool = CHIP_TONE_TABLE["high_importance"]
    elif sentiment in CHIP_TONE_TABLE:
        pool = CHIP_TONE_TABLE[sentiment]
    elif hour >= 23 or hour < 4:
        pool = CHIP_TONE_TABLE["late_night"]
    else:
        pool = CHIP_TONE_TABLE["neutral"]

    return random.choice(pool)


def build_chip_line(enriched):
    """Unified Chip line generator."""
    starter = choose_chip_starter(enriched)

    summary = enriched.get("summary") or enriched.get("headline", "")
    summary = summary.strip()

    if not summary.endswith("."):
        summary += "."

    # Combine
    line = f"{starter} {summary}"

    # Apply tone shaping (A-4)
    tone_weight = compute_chip_tone_weight(enriched)
    line = apply_chip_tone_to_line(line, tone_weight)

    # --- A-14: Chip Macro Context Model ---
    from script_engine.hybrid_tone.macro_model import compute_macro_context
    macro = compute_macro_context(enriched)
    if macro:
        line = f"{line} {macro}"

    # --- A-15: Multi-Story Consensus Model ---
    try:
        from script_engine.hybrid_tone.consensus_engine import compute_story_consensus
        recent = enriched.get("recent_stories", [])
        consensus = compute_story_consensus(recent, enriched)
        if consensus:
            line = f"{line} {consensus}"
    except Exception:
        pass

    # --- A-16: Story Cluster Analysis (Vector Similarity) ---
    try:
        from script_engine.hybrid_tone.cluster_engine import detect_story_cluster
        recent = enriched.get("recent_stories", [])
        cluster = detect_story_cluster(enriched, recent)

        if cluster.get("cluster_line"):
            line = f"{line} {cluster['cluster_line']}"
    except Exception:
        pass

    # --- A-17: Worldview Bias Layer ---
    try:
        from script_engine.hybrid_tone.bias_worldview import apply_worldview_bias
        worldview = apply_worldview_bias(enriched)
        line = f"{line} {worldview}"
    except Exception:
        pass

    # A-13 — Chip worldview bias injection
    from script_engine.hybrid_tone.bias_engine import compute_chip_bias
    bias = compute_chip_bias(enriched)
    if bias:
        line = f"{line} {bias}"

    # === A-18-2: Memory-aware continuity injection ===
    from character_brain.memory_engine import load_memory

    mem = load_memory()
    recent = mem.get("recent_headlines", [])[-10:]  # last ~10 for safety
    clusters = mem.get("story_clusters", [])

    continuity_fragments = []

    # If the same domain has appeared several times lately
    domain = enriched.get("domain")
    if domain and clusters.count(domain) >= 3:
        continuity_fragments.append(f"We’ve been seeing a lot of {domain} movement lately.")

    # If this headline resembles one from the past hour (simple heuristic)
    hl = enriched.get("headline", "").lower()
    if hl:
        for old in recent[-5:]:
            if old.lower() != hl and any(word in hl for word in old.lower().split()[:3]):
                continuity_fragments.append("This connects to earlier developments we covered.")
                break

    # Merge continuity fragments into line *if any exist*
    if continuity_fragments:
        cont = " ".join(continuity_fragments)
        line = f"{line} {cont}"

    return " ".join(line.split()).strip()
