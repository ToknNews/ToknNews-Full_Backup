#!/usr/bin/env python3
"""
run_semantic_clustering.py

CANONICAL (PRODUCTION SAFE):
- Time-windowed clustering
- Hard cap on TF-IDF batch size
- Prevents all cosine OOM cases
- Usable as BOTH a script and a library
- STRICT return type enforcement (List[dict])
"""

import json
import time
from pathlib import Path
from typing import List
from .clustering_engine import cluster_pipeline

# -------------------------
# PATHS
# -------------------------
STORY_LAKE_PATH = Path("/opt/toknnews/data/stories/story_lake.json")
CLUSTER_PATH = Path("/opt/toknnews/data/stories/story_clusters.json")
REFINED_PATH = Path("/opt/toknnews/data/stories/story_refined_clusters.json")

# -------------------------
# WINDOW + SAFETY LIMITS
# -------------------------
WINDOW_SIZE = 6 * 60 * 60        # 6 hours
WINDOW_OVERLAP = 60 * 60         # 1 hour
MAX_WINDOW_STORIES = 800         # HARD SAFETY CAP

# =====================================================
# LIBRARY ENTRYPOINT (USED BY PREVIEW)
# =====================================================
def run_semantic_clustering(stories: List[dict]) -> List[dict]:
    """
    Run semantic clustering on a bounded list of stories.

    GUARANTEE:
    - Always returns List[dict]
    - Never returns bool / None
    """

    if not stories or not isinstance(stories, list):
        return []

    stories = [s for s in stories if isinstance(s, dict) and s.get("timestamp")]
    if not stories:
        return []

    stories.sort(key=lambda s: s["timestamp"])

    clusters_out: List[dict] = []
    start_idx = 0

    while start_idx < len(stories):
        window_start = stories[start_idx]["timestamp"]
        window_end = window_start + WINDOW_SIZE

        window = []
        idx = start_idx

        while idx < len(stories) and stories[idx]["timestamp"] <= window_end:
            window.append(stories[idx])
            idx += 1

        print(
            f"[CLUSTER] Window {time.ctime(window_start)} → "
            f"{time.ctime(window_end)} ({len(window)} stories)"
        )

        # -----------------------------
        # SAFE CLUSTER EXECUTION
        # -----------------------------
        def _safe_cluster(batch):
            try:
                result = cluster_pipeline(batch)
                if isinstance(result, list):
                    return result
                else:
                    print(
                        "[CLUSTER][WARN] cluster_pipeline returned "
                        f"{type(result).__name__}; ignoring batch"
                    )
                    return []
            except Exception as e:
                print(f"[CLUSTER][ERROR] cluster_pipeline failed: {e}")
                return []

        if len(window) > MAX_WINDOW_STORIES:
            print(
                f"[CLUSTER] Window too large ({len(window)}). "
                f"Chunking into batches of {MAX_WINDOW_STORIES}"
            )

            for i in range(0, len(window), MAX_WINDOW_STORIES):
                batch = window[i:i + MAX_WINDOW_STORIES]
                clusters_out.extend(_safe_cluster(batch))
        else:
            clusters_out.extend(_safe_cluster(window))

        # Advance with overlap
        next_start_time = window_end - WINDOW_OVERLAP
        while start_idx < len(stories) and stories[start_idx]["timestamp"] < next_start_time:
            start_idx += 1

    return clusters_out

# =====================================================
# SCRIPT ENTRYPOINT (CLI)
# =====================================================
def main():
    if not STORY_LAKE_PATH.exists():
        raise FileNotFoundError(f"Missing story lake: {STORY_LAKE_PATH}")

    stories = json.loads(STORY_LAKE_PATH.read_text())
    print(f"[CLUSTER] Loaded {len(stories)} stories")

    clusters = run_semantic_clustering(stories)

    CLUSTER_PATH.parent.mkdir(parents=True, exist_ok=True)
    CLUSTER_PATH.write_text(json.dumps(clusters, indent=2))
    REFINED_PATH.write_text(json.dumps(clusters, indent=2))

    print(f"[CLUSTER] Wrote {len(clusters)} clusters")

if __name__ == "__main__":
    main()
