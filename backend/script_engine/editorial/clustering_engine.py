#!/usr/bin/env python3
"""
clustering_engine.py — ToknNews Semantic Clustering (PRODUCTION)

Design:
- Pass 1: TF-IDF cosine similarity (fast candidate grouping)
- Pass 2: GPT refinement ONLY for small clusters (same real-world event check)
- Enhancement: Attach raw Moralis events to onchain_synth clusters
- HARD SAFETY: GPT never runs on large clusters
- SAFE: never drops stories
- Canon-compliant with TRANSFER_BRAIN_V3
"""

import os
import json
import re
from uuid import uuid4
from dotenv import load_dotenv

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

import openai
ENABLE_GPT_CLUSTERING = os.getenv("ENABLE_GPT_CLUSTERING", "false").lower() == "true"

# ------------------------------------------------------------
# ENV
# ------------------------------------------------------------
load_dotenv("/opt/toknnews/.env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip()
if OPENAI_API_KEY:
    openai.api_key = OPENAI_API_KEY

GPT_CLUSTER_MODEL = os.getenv("GPT_CLUSTER_MODEL", "gpt-4.1").strip()
DEBUG_CLUSTER = os.getenv("DEBUG_CLUSTER", "false").lower() == "true"

# ------------------------------------------------------------
# HARD SAFETY LIMITS (NON-NEGOTIABLE)
# ------------------------------------------------------------
MAX_GPT_CLUSTER_SIZE = 30          # GPT refinement cutoff
ONCHAIN_ATTACH_WINDOW_SEC = 900    # ±15 minutes

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------
def _story_headline(s: dict) -> str:
    return (s.get("headline") or s.get("title") or "").strip()

def _story_summary(s: dict) -> str:
    return (s.get("summary") or s.get("description") or "").strip()

def _combined_text(s: dict) -> str:
    h = _story_headline(s)
    d = _story_summary(s)
    combo = f"{h} {d}".strip()
    return combo if combo else " "

def _strip_code_fences(txt: str) -> str:
    if not txt:
        return ""
    txt = txt.strip()
    txt = re.sub(r"^```(?:json)?\s*", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s*```$", "", txt)
    return txt.strip()

def _ensure_ids(stories: list) -> list:
    """
    Ensure each story has a stable internal id.
    Never overwrites an existing id.
    """
    out = []
    for s in stories:
        if not isinstance(s, dict):
            continue
        if not s.get("id"):
            s = dict(s)
            s["id"] = str(uuid4())
        out.append(s)
    return out

# ------------------------------------------------------------
# PASS 1 — FAST SEMANTIC GROUPING
# ------------------------------------------------------------
def basic_grouping(stories: list, threshold: float = 0.05) -> list:
    stories = _ensure_ids(stories)

    texts = [_combined_text(s) for s in stories]
    vectorizer = TfidfVectorizer(stop_words="english")
    X = vectorizer.fit_transform(texts)

    sim_matrix = cosine_similarity(X)

    clusters = []
    assigned = set()

    for i in range(len(stories)):
        if i in assigned:
            continue

        cluster = [stories[i]]
        assigned.add(i)

        for j in range(i + 1, len(stories)):
            if j in assigned:
                continue
            if sim_matrix[i][j] > threshold:
                cluster.append(stories[j])
                assigned.add(j)

        clusters.append(cluster)

    return clusters

# ------------------------------------------------------------
# PASS 2 — GPT REFINEMENT (SMALL CLUSTERS ONLY)
# ------------------------------------------------------------
def refine_with_gpt(clusters: list, all_stories: list) -> list:
    refined = []

    if not ENABLE_GPT_CLUSTERING or not openai.api_key:
        for c in clusters:
            refined.append({
                "id": str(uuid4()),
                "stories": c
            })
        return refined

    for c in clusters:

        # --------------------------------------------------
        # HARD GPT SAFETY GUARD
        # --------------------------------------------------
        if len(c) > MAX_GPT_CLUSTER_SIZE:
            refined.append({
                "id": str(uuid4()),
                "stories": c
            })
            continue

        # Single-item clusters passthrough
        if len(c) <= 1:
            refined.append({
                "id": str(uuid4()),
                "stories": c
            })
            continue

        headline_map = {}
        ordered_headlines = []

        for s in c:
            h = _story_headline(s)
            if not h:
                h = f"(no_headline:{s.get('id')})"
            headline_map[h] = s
            ordered_headlines.append(h)

        formatted = "\n".join(
            f"- {h} :: {_story_summary(headline_map[h])}"
            for h in ordered_headlines
        )

        prompt = (
            "You are an editorial clustering agent.\n\n"
            "Below is a list of news stories (headline + summary).\n\n"
            f"{formatted}\n\n"
            "Task:\n"
            "- Group stories ONLY if they describe the SAME real-world event.\n"
            "- If related but distinct, keep them separate.\n\n"
            "Output JSON ONLY as a list of clusters, each cluster a list of EXACT headline strings.\n"
            "Every headline must appear exactly once.\n"
        )

        if DEBUG_CLUSTER:
            print("\n[DEBUG] GPT CLUSTER PROMPT:\n", prompt)

        try:
            resp = openai.ChatCompletion.create(
                model=GPT_CLUSTER_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=600,
            )

            raw = _strip_code_fences(resp["choices"][0]["message"]["content"])
            parsed = json.loads(raw)

            used = set()

            for subset in parsed:
                matched = []
                for title in subset:
                    if title in headline_map and title not in used:
                        matched.append(headline_map[title])
                        used.add(title)

                if matched:
                    refined.append({
                        "id": str(uuid4()),
                        "stories": matched
                    })

            # Preserve any unassigned stories
            for h in ordered_headlines:
                if h not in used:
                    refined.append({
                        "id": str(uuid4()),
                        "stories": [headline_map[h]]
                    })

        except Exception as e:
            print(f"[Cluster GPT Error] {e}")
            refined.append({
                "id": str(uuid4()),
                "stories": c
            })

    # ------------------------------------------------------------
    # ATTACH RAW MORALIS EVENTS TO ONCHAIN SYNTH CLUSTERS
    # ------------------------------------------------------------
    final_clusters = []

    for cluster in refined:
        stories = list(cluster["stories"])

        synth = next(
            (s for s in stories if s.get("source") == "onchain_synth_v1"),
            None
        )

        if synth:
            synth_ts = synth.get("timestamp", 0)

            for candidate in all_stories:
                if candidate.get("source") != "moralis_stream":
                    continue
                if abs(candidate.get("timestamp", 0) - synth_ts) <= ONCHAIN_ATTACH_WINDOW_SEC:
                    if candidate not in stories:
                        stories.append(candidate)

        final_clusters.append({
            "id": cluster["id"],
            "stories": stories
        })

    return final_clusters

# ------------------------------------------------------------
# PIPELINE ENTRY
# ------------------------------------------------------------
def cluster_pipeline(stories: list, threshold: float = 0.45) -> list:
    fast_pass = basic_grouping(stories, threshold=threshold)
    refined = refine_with_gpt(fast_pass, stories)
    return refined

# ------------------------------------------------------------
# CLI
# ------------------------------------------------------------
if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--infile", default="/opt/toknnews/data/stories/story_lake.json")
    ap.add_argument("--outfile", default="/opt/toknnews/data/stories/story_clusters.json")
    ap.add_argument("--threshold", type=float, default=0.45)
    args = ap.parse_args()

    if not os.path.exists(args.infile):
        raise FileNotFoundError(f"No input file: {args.infile}")

    with open(args.infile, "r") as f:
        data = json.load(f)

    if not isinstance(data, list):
        raise ValueError("Input must be a JSON list")

    clusters = cluster_pipeline(data, threshold=args.threshold)

    os.makedirs(os.path.dirname(args.outfile), exist_ok=True)
    with open(args.outfile, "w") as f:
        json.dump(clusters, f, indent=2)

    print(f"[CLUSTER] Loaded {len(data)} stories")
    print(f"[CLUSTER] Wrote {len(clusters)} clusters → {args.outfile}")
