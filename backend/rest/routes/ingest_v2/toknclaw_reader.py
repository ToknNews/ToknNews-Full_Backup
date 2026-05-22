#!/usr/bin/env python3

import json
import subprocess
import tempfile
import time

TOKNCLAW_HOST = "root@5.161.192.62"
TOKNCLAW_PATH = "/opt/toknclaw/data/snapshots"


def fetch_toknclaw_signals():

    try:

        # Find newest snapshot on ToknClaw
        cmd = [
            "ssh",
            TOKNCLAW_HOST,
            f"ls -t {TOKNCLAW_PATH}/*.json | head -1"
        ]

        result = subprocess.check_output(cmd).decode().strip()

        if not result:
            print("[TOKNCLAW] No snapshots found")
            return []

        # Copy newest snapshot locally
        tmp_file = tempfile.mktemp(suffix=".json")

        subprocess.check_call([
            "scp",
            f"{TOKNCLAW_HOST}:{result}",
            tmp_file
        ])

        with open(tmp_file) as f:
            snap = json.load(f)

    except Exception as e:
        print("[TOKNCLAW] fetch failed:", e)
        return []

    signals = snap.get("signals", [])
    analysis = snap.get("analysis", {})
    metrics = snap.get("metrics", {})
    memory = snap.get("memory", {})
    deltas = snap.get("deltas", {})

    stories = []

    for s in signals:

        headline = s.get("title") or ""
        summary = s.get("summary") or "Signal detected from ToknClaw intelligence layer."

        entity = s.get("entity")
        signal_type = s.get("signal_type")
        exchange = s.get("exchange")
        value_usd = s.get("value_usd")

        if isinstance(value_usd, (int, float)):
            headline = f"${value_usd:,.0f} {headline}"

        entities = []
        if entity:
            entities.append({
                "name": entity,
                "symbol": entity,
                "mentions": 5,
                "sentiment_score": None
            })

        stories.append({

            "headline": headline,
            "summary": summary,
            "source": "toknclaw",
            "domain": "onchain",
            "timestamp": time.time(),
            "importance": 8.5,

            "entities": entities,

            "semantic_keys": {
                "domain": "onchain",
                "assets": [entity] if entity else [],
                "event_type": signal_type,
                "actors": ["whales"] if signal_type == "whale_transfer" else [],
                "time_scope": "immediate",
                "confidence": 0.9
            },

            "signal_data": {
                "entity": entity,
                "signal_type": signal_type,
                "exchange": exchange,
                "value_usd": value_usd
            },

            "toknclaw_context": {
                "analysis": analysis,
                "metrics": metrics,
                "memory": memory,
                "deltas": deltas
            }
        })

    print(f"[TOKNCLAW] {len(stories)} signals ingested")

    return stories
