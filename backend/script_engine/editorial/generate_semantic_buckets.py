#!/usr/bin/env python3
"""
generate_semantic_buckets.py

Bridge between semantic clustering (pass 1) and GPT refinement (pass 2).

Input:
  /opt/toknnews/data/stories/story_clusters.json

Output:
  /opt/toknnews/data/stories/story_semantic_buckets.json

This does NOT change semantics.
It only reformats clusters into the contract expected by gpt_refine_clusters.py.
"""

import json
from pathlib import Path

INPUT_PATH = Path("/opt/toknnews/data/stories/story_clusters.json")
OUTPUT_PATH = Path("/opt/toknnews/data/stories/story_semantic_buckets.json")

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Missing clusters: {INPUT_PATH}")

    clusters = json.loads(INPUT_PATH.read_text())
    print(f"[BUCKET] Loaded {len(clusters)} clusters")

    buckets = []

    for c in clusters:
        stories = c.get("stories", [])
        if not stories:
            continue

        buckets.append({
            "bucket_id": c.get("id"),
            "stories": stories
        })

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(buckets, indent=2))

    print(f"[BUCKET] Wrote {len(buckets)} semantic buckets → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
