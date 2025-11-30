#!/usr/bin/env python3
"""
ToknNews Memory Engine (v1)

Handles:
- short-term memory decay
- domain heatmap weighting
- cluster pruning
- recency-preference for continuity
"""

import json
import os
from datetime import datetime, timedelta

BASE_DIR = os.path.dirname(__file__)
MEM_PATH = os.path.join(BASE_DIR, "character_memory.json")


# -------------------------------
# Load / Save
# -------------------------------
def load_memory():
    if not os.path.exists(MEM_PATH):
        return {}
    try:
        with open(MEM_PATH, "r") as f:
            return json.load(f)
    except:
        return {}


def save_memory(mem):
    try:
        with open(MEM_PATH, "w") as f:
            json.dump(mem, f, indent=2)
    except:
        pass


# -------------------------------
# Decay Engine
# -------------------------------
def decay_memory(mem):
    """
    Applies natural decay to stored memory items.
    Older items lose weight so only fresh/ongoing themes matter.
    """

    cutoff = datetime.utcnow() - timedelta(hours=3)
    new_items = []

    for item in mem.get("recent_items", []):
        ts = item.get("timestamp")
        try:
            dt = datetime.fromisoformat(ts)
        except:
            continue

        # Hard drop if extremely old
        if dt < cutoff:
            continue

        # Time-weighted decay factor
        age_minutes = (datetime.utcnow() - dt).total_seconds() / 60
        decay_factor = max(0.1, 1.0 - (age_minutes / 180))  # ~3hr decay

        item["weight"] = round(item.get("weight", 1.0) * decay_factor, 4)
        new_items.append(item)

    mem["recent_items"] = new_items
    return mem


# -------------------------------
# Cluster Cleanup
# -------------------------------
def clean_clusters(mem):
    """
    Removes old domain clusters so Chip doesn't think
    old surges are still active.
    """
    cutoff = datetime.utcnow() - timedelta(hours=1)
    new_clusters = []

    for c in mem.get("story_clusters", []):
        try:
            dt = datetime.fromisoformat(c.get("timestamp"))
        except:
            continue

        if dt >= cutoff:
            new_clusters.append(c)

    mem["story_clusters"] = new_clusters
    return mem


# -------------------------------
# Domain Heatmap
# -------------------------------
def update_domain_heat(mem, domain):
    """
    Maintains weighted domain heat:
    - increments on new story
    - decays over time
    """

    heat = mem.setdefault("domain_heatmap", {})
    now = datetime.utcnow()

    # Light bump for mention
    heat.setdefault(domain, {"score": 0.0, "updated": now.isoformat()})
    heat[domain]["score"] += 1.0

    # Apply decay to all other domains
    for d, info in heat.items():
        try:
            dt = datetime.fromisoformat(info["updated"])
        except:
            continue

        age_minutes = (datetime.utcnow() - dt).total_seconds() / 60
        decay_factor = max(0.05, 1.0 - (age_minutes / 240))  # 4hr decay
        info["score"] *= decay_factor
        info["updated"] = now.isoformat()

    mem["domain_heatmap"] = heat
    return mem


# -------------------------------
# Update Memory Entry Point
# -------------------------------
def update_memory_with_story(enriched):
    mem = load_memory()

    mem.setdefault("recent_items", [])
    mem.setdefault("story_clusters", [])
    mem.setdefault("domain_heatmap", {})

    now = datetime.utcnow().isoformat()

    # Store item
    mem["recent_items"].append({
        "headline": enriched.get("headline", ""),
        "domain": enriched.get("domain", "general"),
        "timestamp": now,
        "weight": 1.0,
    })

    # Cluster track
    mem["story_clusters"].append({
        "domain": enriched.get("domain", "general"),
        "timestamp": now
    })

    # Apply engines
    mem = decay_memory(mem)
    mem = clean_clusters(mem)
    mem = update_domain_heat(mem, enriched.get("domain", "general"))

    save_memory(mem)
    return mem
