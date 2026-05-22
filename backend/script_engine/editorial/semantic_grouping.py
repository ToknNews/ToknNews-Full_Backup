#!/usr/bin/env python3
"""
semantic_grouping.py
ToknNews — Semantic Pre-Grouping Layer (Step 4)

Purpose:
- Group stories by semantic_keys into candidate buckets
- NO GPT
- NO deletion
- NO dedupe
"""

import json
import hashlib
from collections import defaultdict
from datetime import datetime, timezone

INPUT_PATH = "/opt/toknnews/data/stories/story_lake.json"
OUTPUT_PATH = "/opt/toknnews/data/stories/story_semantic_buckets.json"

TIME_WINDOW_HOURS = 48  # adjustable later


def _bucket_hash(domain, event_type, assets, time_window):
    base = f"{domain}|{event_type}|{','.join(sorted(assets))}|{time_window}"
    return hashlib.sha1(base.encode()).hexdigest()[:16]


def _time_bucket(ts):
    """
    Buckets timestamps into coarse windows (e.g. 48h)
    """
    if not ts:
        return "unknown"
    try:
        dt = datetime.fromtimestamp(ts, tz=timezone.utc)
        return f"{dt.year}-{dt.month}-{dt.day}"
    except Exception:
        return "unknown"


def build_semantic_buckets(stories):
    buckets = defaultdict(list)

    for story in stories:
        sk = story.get("semantic_keys") or {}

        domain = sk.get("domain", "unknown")
        event_type = sk.get("event_type", "unknown")
        assets = sk.get("assets") or []
        time_scope = _time_bucket(story.get("timestamp"))

        bucket_id = _bucket_hash(domain, event_type, assets, time_scope)

        buckets[bucket_id].append(story)

    return buckets


def main():
    with open(INPUT_PATH) as f:
        stories = json.load(f)

    print(f"[SEMANTIC] Loaded {len(stories)} stories")

    buckets = build_semantic_buckets(stories)

    output = []
    for bucket_id, items in buckets.items():
        output.append({
            "bucket_id": bucket_id,
            "story_count": len(items),
            "stories": items
        })

    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, indent=2)

    avg = round(sum(len(b["stories"]) for b in output) / max(len(output), 1), 2)

    print(f"[SEMANTIC] Created {len(output)} candidate buckets")
    print(f"[SEMANTIC] Avg bucket size: {avg}")
    print(f"[SEMANTIC] Wrote → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
