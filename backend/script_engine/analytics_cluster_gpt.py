#!/usr/bin/env python3
"""
analytics_cluster_gpt.py
ToknNews — GPT Narrative Clustering Engine (Optimized)
"""

import json
import time
from pathlib import Path
from openai import OpenAI
import os

from backend.script_engine.story_bank import get_recent_for_clustering

# Diagnostics log
LOG_PATH = Path("/opt/toknnews/data/analytics/gpt_diagnostics.log")


def log(msg):
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(msg + "\n")


def pretty(obj):
    return json.dumps(obj, indent=2)


def generate_clusters(onchain=None):
    """
    Returns:
        {
          "clusters": [...],
          "source": "gpt" | "gpt_failure",
          "ts": timestamp
        }
    """

    # ----------------------------------------------------
    # 1. Pull the optimized story slice (max ~40)
    # ----------------------------------------------------
    stories = get_recent_for_clustering(max_items=40)
    log("\n======= NEW CLUSTER RUN =======")
    log(f"Selected stories: {len(stories)}")

    # If no stories, return clean fallback
    if not stories:
        return {"clusters": [], "source": "empty", "ts": time.time()}

    # ----------------------------------------------------
    # 2. Build structured clusters
    # ----------------------------------------------------
    structured_clusters = {}
    for s in stories:
        d = s.get("domain", "general")
        structured_clusters.setdefault(d, {"domain": d, "stories": []})
        structured_clusters[d]["stories"].append({
            "headline": s.get("headline", ""),
            "summary": s.get("summary", ""),
            "domain": d,
            "sentiment": s.get("sentiment", "Neutral"),
            "importance": s.get("importance", 5.0),
            "anchors": s.get("anchors", []),
            "source": s.get("source", ""),
            "timestamp": s.get("timestamp", 0),
            "breaking": s.get("breaking", False),
        })

    payload = {
        "structured_clusters": structured_clusters,
        "onchain": onchain or {},
    }

    log("Payload preview:\n" + pretty({"sample": list(structured_clusters.keys())[:4]}))

    # ----------------------------------------------------
    # 3. Build GPT prompt
    # ----------------------------------------------------
    prompt = (
        "You are a crypto narrative intelligence analyst.\n"
        "ToknNews has grouped stories into clusters. Your job:\n"
        "- Name the narrative\n"
        "- Summarize it in 1 sentence\n"
        "- Provide 2 reasons\n"
        "- List key headlines\n\n"
        "INPUT JSON:\n"
        f"{json.dumps(payload, indent=2)}\n\n"
        "OUTPUT RULES:\n"
        "Return ONLY valid JSON:\n"
        "{\n"
        '  \"clusters\": [\n'
        "    {\n"
        '      \"name\": \"...\",\n'
        '      \"summary\": \"...\",\n'
        '      \"reasons\": [\"...\", \"...\"],\n'
        '      \"stories\": [\"headline1\", \"headline2\"]\n'
        "    }\n"
        "  ],\n"
        '  \"source\": \"gpt\"\n'
        "}\n"
    )

    # ----------------------------------------------------
    # 4. Run GPT (using known working model)
    # ----------------------------------------------------
    api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=api_key)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",        # reliable access
            messages=[
                {"role": "system", "content": "You are a crypto narrative intelligence engine."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=1000,
            timeout=20,  # avoid hanging ingestion
        )

        raw = response.choices[0].message.content.strip()
        log("RAW GPT OUTPUT:\n" + raw[:1200])

        data = json.loads(raw)

        return {
            "clusters": data.get("clusters", []),
            "source": "gpt",
            "ts": time.time(),
        }

    except Exception as e:
        log("=== GPT ERROR ===")
        log(str(e))

        return {
            "clusters": [],
            "source": "gpt_failure",
            "error": str(e),
            "ts": time.time(),
        }


