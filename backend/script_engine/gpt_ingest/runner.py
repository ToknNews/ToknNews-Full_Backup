import json
import time
from backend.script_engine.gpt_ingest.queries import GPT_INGEST_QUERIES
from backend.script_engine.utils.story_lake import (
    SHARDS,
    append_story_sharded,
)
from backend.script_engine.utils.story_lake import _load as load_json
from backend.runtime.gpt_client import get_gpt_client
from backend.script_engine.utils.story_lake import SHARDS, _load


ONCHAIN_WINDOW = 30 * 60      # 30 minutes
RSS_WINDOW = 2 * 60 * 60     # 2 hours
GPT_TTL_SECONDS = 24 * 3600  # 24 hours


def collect_inputs(now):
    inputs = {
        "onchain": [],
        "rss": [],
    }

    for s in load_json(SHARDS["onchain"]):
        if now - s.get("timestamp", 0) <= ONCHAIN_WINDOW:
            inputs["onchain"].append(s)

    for s in load_json(SHARDS["rss"]):
        if now - s.get("timestamp", 0) <= RSS_WINDOW:
            inputs["rss"].append(s)

    return inputs


def build_prompt(query, inputs):
    visible = []
    for src in query["inputs"]:
        visible.extend(inputs.get(src, []))

    payload = json.dumps(visible[:10], indent=2)

    return f"""
You are a crypto market intelligence system.

Task:
{query["purpose"]}

Rules:
- Do NOT invent facts
- Do NOT restate existing headlines
- Only output if a real narrative exists
- Reference supporting signals explicitly

Signals:
{payload}

Output JSON ONLY or null:
{{
  "headline": "...",
  "summary": "...",
  "confidence_reasoning": "...",
  "supporting_ids": ["tx_hash or timestamp"],
  "domain": "markets | macro | regulation"
}}
"""

DEDUP_WINDOW_SECONDS = 6 * 3600  # 6 hours


def apply_soft_dedup(new_story, now_ts):
    """
    Soft-deduplicate GPT stories.
    Reduces importance/confidence for repeated narratives.
    """

    gpt_stories = _load(SHARDS["gpt"])

    for prev in reversed(gpt_stories):
        # Only consider recent GPT stories
        if now_ts - prev.get("timestamp", 0) > DEDUP_WINDOW_SECONDS:
            break

        # Must be same GPT analyst/query
        if prev.get("query_id") != new_story.get("query_id"):
            continue

        prev_ids = set(prev.get("supporting_ids", []))
        new_ids = set(new_story.get("supporting_ids", []))

        if not prev_ids or not new_ids:
            continue

        overlap_ratio = len(prev_ids & new_ids) / max(len(new_ids), 1)

        if overlap_ratio >= 0.5:
            new_story["importance"] = max(
                2.0, round(new_story["importance"] * 0.7, 2)
            )
            new_story["confidence"] = round(
                new_story.get("confidence", 1.0) * 0.75, 2
            )
            new_story["repeat_of"] = prev.get("timestamp")
            new_story["repeat_count"] = prev.get("repeat_count", 1) + 1

            return new_story

    return new_story

def expire_old_gpt_stories(now_ts):
    """
    Remove GPT stories older than TTL.
    """
    gpt_path = SHARDS["gpt"]
    stories = _load(gpt_path)

    fresh = [
        s for s in stories
        if now_ts - s.get("timestamp", 0) <= GPT_TTL_SECONDS
    ]

    if len(fresh) != len(stories):
        _write(gpt_path, fresh)

def run_gpt_ingest():
    now = time.time()
    expire_old_gpt_stories(now)
    inputs = collect_inputs(now)
    gpt = get_gpt_client()

    for query in GPT_INGEST_QUERIES:
        prompt = build_prompt(query, inputs)

        try:
            response = gpt.complete(prompt).strip()
            if response.lower() == "null":
                continue

            data = json.loads(response)

            story = {
                "headline": data["headline"],
                "summary": data["summary"],
                "domain": data["domain"],
                "sentiment": "Neutral",
                "importance": query["importance_cap"],
                "anchors": ["chip"],
                "source": "gpt_ingest_v1",
                "timestamp": now,
                "supporting_ids": data["supporting_ids"],
                "confidence_reasoning": data["confidence_reasoning"],
                "query_id": query["id"],
            }

            story = apply_soft_dedup(story, now)
            append_story_sharded(story)

        except Exception:
            continue


if __name__ == "__main__":
    run_gpt_ingest()
