#!/usr/bin/env python3
"""
gpt_refine_clusters.py
ToknNews — GPT Semantic Cluster Refinement (Step 5)
"""

import json
import os
import openai
from uuid import uuid4
from dotenv import load_dotenv

load_dotenv("/opt/toknnews/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

INPUT_PATH = "/opt/toknnews/data/stories/story_semantic_buckets.json"
OUTPUT_PATH = "/opt/toknnews/data/stories/story_refined_clusters.json"

MODEL = "gpt-4.1"
MAX_STORIES_PER_PROMPT = 10  # hard safety cap


def build_prompt(stories):
    lines = []
    for s in stories:
        headline = s.get("headline") or s.get("title") or "UNKNOWN"
        domain = s.get("domain", "unknown")
        lines.append(f"- {headline} [{domain}]")

    joined = "\n".join(lines)

    return f"""
You are an editorial clustering agent.

Below is a list of news stories.

Group stories ONLY if they describe the SAME real-world event.
If they are related but distinct, keep them separate.

Return JSON ONLY in this format:
[
  ["Exact Headline A", "Exact Headline B"],
  ["Exact Headline C"]
]

Rules:
- Use headlines EXACTLY as written
- Do NOT invent headlines
- Do NOT drop any headlines

Stories:
{joined}
""".strip()


def refine_bucket(bucket):
    stories = bucket["stories"]

    # Safety: small buckets pass through untouched
    if len(stories) <= 1:
        return [{
            "cluster_id": str(uuid4()),
            "stories": stories
        }]

    prompt = build_prompt(stories)

    try:
        print("\n[GPT REFINE] Prompt:\n", prompt)

        resp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
        )

        raw = resp.choices[0].message.content.strip()
        parsed = json.loads(raw)

        used = set()
        refined = []

        for group in parsed:
            matched = [s for s in stories if (s.get("headline") or s.get("title")) in group]
            if matched:
                refined.append({
                    "cluster_id": str(uuid4()),
                    "stories": matched
                })
                for s in matched:
                    used.add(id(s))

        # CRITICAL: preserve leftovers
        for s in stories:
            if id(s) not in used:
                refined.append({
                    "cluster_id": str(uuid4()),
                    "stories": [s]
                })

        return refined

    except Exception as e:
        print("[GPT REFINE ERROR]", e)
        # Hard fallback: preserve bucket as-is
        return [{
            "cluster_id": str(uuid4()),
            "stories": stories
        }]


def main():
    with open(INPUT_PATH) as f:
        buckets = json.load(f)

    print(f"[GPT REFINE] Loaded {len(buckets)} semantic buckets")

    final_clusters = []

    for bucket in buckets:
        stories = bucket["stories"]

        # Chunk large buckets
        for i in range(0, len(stories), MAX_STORIES_PER_PROMPT):
            chunk = stories[i:i + MAX_STORIES_PER_PROMPT]
            refined = refine_bucket({"stories": chunk})
            final_clusters.extend(refined)

    with open(OUTPUT_PATH, "w") as f:
        json.dump(final_clusters, f, indent=2)

    print(f"[GPT REFINE] Wrote {len(final_clusters)} refined clusters → {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
