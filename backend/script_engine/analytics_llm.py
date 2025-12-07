#!/usr/bin/env python3
"""
LLM Analytics Engine
Runs GPT-powered narrative metrics:
 - cluster coherence scoring
 - narrative drift detection
 - narrative velocity index
 - feedback grade (clarity / novelty / risk)
"""

import json
import time
from openai import OpenAI

client = OpenAI()

# -------------------------------
# Helpers
# -------------------------------

def _gpt(prompt, max_tokens=400):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.2,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return json.dumps({"error": str(e)})


# -------------------------------
# 1. Coherence Score
# -------------------------------

def coherence_score(cluster):
    """
    cluster = { "name": , "stories": [ {headline}, ... ] }
    """
    prompt = f"""
You are scoring the internal coherence of a narrative cluster.
Rate how well the following headlines belong together.
Output JSON only: {{"coherence": 0-1}}

Cluster:
{json.dumps(cluster, indent=2)}
"""
    out = _gpt(prompt)
    try:
        return json.loads(out).get("coherence", 0.0)
    except:
        return 0.0


# -------------------------------
# 2. Narrative Drift
# -------------------------------

def narrative_drift(previous_cluster, new_cluster):
    prompt = f"""
Compare two narrative clusters. How much has the story direction shifted?
0.0 = same narrative, 1.0 = completely different.

Output JSON: {{"drift": 0-1}}

Previous:
{json.dumps(previous_cluster, indent=2)}

New:
{json.dumps(new_cluster, indent=2)}
"""
    out = _gpt(prompt)
    try:
        return json.loads(out).get("drift", 0.0)
    except:
        return 0.0


# -------------------------------
# 3. Velocity Index
# -------------------------------
def velocity_index(story_count_last_hour, story_count_now):
    if story_count_now == 0:
        return 0.0
    return (story_count_now - story_count_last_hour) / max(story_count_now, 1)


# -------------------------------
# 4. GPT Feedback Grade
# -------------------------------

def feedback_grade(cluster):
    prompt = f"""
Grade this narrative cluster on:
 - clarity
 - novelty
 - risk of hallucination
 - usefulness for news

Return a JSON object:

{{
  "grade": "A-F",
  "notes": ["...", "..."]
}}

Cluster:
{json.dumps(cluster, indent=2)}
"""
    out = _gpt(prompt)
    try:
        return json.loads(out)
    except:
        return {"grade": "C", "notes": ["Parse error"]}


# -------------------------------
# MASTER FUNCTION
# -------------------------------

def run_llm_analytics(clusters, prev_clusters=None, story_velocity=None):
    """
    clusters = list of cluster dicts
    prev_clusters = last cycle’s clusters
    """
    results = []
    for i, c in enumerate(clusters):

        prev = prev_clusters[i] if prev_clusters and i < len(prev_clusters) else None

        coherence = coherence_score(c)
        drift = narrative_drift(prev, c) if prev else 0.0
        grade = feedback_grade(c)

        velocity = velocity_index(
            story_velocity.get(c["name"], 0),
            len(c.get("stories", []))
        ) if story_velocity else 0.0

        results.append({
            "name": c["name"],
            "coherence": coherence,
            "drift": drift,
            "velocity": velocity,
            "grade": grade,
        })

    return {
        "ts": time.time(),
        "analytics": results
    }
