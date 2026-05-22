#!/usr/bin/env python3
import json
import time
from uuid import uuid4
from collections import defaultdict
from pathlib import Path

INPUT_PATH = Path("/opt/toknnews/data/stories/story_clusters.json")
OUTPUT_PATH = Path("/opt/toknnews/data/stories/narrative_clusters.json")

MAX_STORIES = 8
TIME_WINDOW_SEC = 86400  # 24h

DOMAIN_ANCHOR = {
    "markets": "chip",
    "macro": "bond",
    "regulation": "lawson",
    "ai": "neura",
    "culture": "bitsy",
    "onchain": "ledger"
}

def load_event_clusters():
    return json.loads(INPUT_PATH.read_text())

def semantic_signature(story):
    return story.get("semantic_keys", {})

def compatible(sig_a, sig_b):
    return (
        bool(set(sig_a.get("assets", [])) & set(sig_b.get("assets", []))) or
        bool(set(sig_a.get("actors", [])) & set(sig_b.get("actors", []))) or
        sig_a.get("event_type") == sig_b.get("event_type")
    )

def resolve_anchors(domains):
    anchors = []
    for d in domains:
        if d in DOMAIN_ANCHOR:
            anchors.append(DOMAIN_ANCHOR[d])
    return list(dict.fromkeys(anchors))[:2]

def build_narratives(event_clusters):
    narratives = []
    used_story_ids = set()

    for cluster in event_clusters:
        stories = cluster["stories"]
        for s in stories:
            if s["id"] in used_story_ids:
                continue

            bucket = [s]
            used_story_ids.add(s["id"])
            sig = semantic_signature(s)

            for other_cluster in event_clusters:
                for o in other_cluster["stories"]:
                    if o["id"] in used_story_ids:
                        continue
                    if len(bucket) >= MAX_STORIES:
                        break
                    if compatible(sig, semantic_signature(o)):
                        bucket.append(o)
                        used_story_ids.add(o["id"])

            domains = list({b["domain"] for b in bucket})
            narratives.append({
                "narrative_cluster_id": str(uuid4()),
                "domains": domains,
                "anchors": resolve_anchors(domains),
                "stories": bucket,
                "created_at": int(time.time())
            })

    return narratives

def main():
    clusters = load_event_clusters()
    narratives = build_narratives(clusters)
    OUTPUT_PATH.write_text(json.dumps(narratives, indent=2))
    print(f"[NARRATIVE] Wrote {len(narratives)} narrative clusters → {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
