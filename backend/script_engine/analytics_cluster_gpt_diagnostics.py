#!/usr/bin/env python3
"""
analytics_cluster_gpt_diagnostics.py
Diagnostic version — logs everything GPT sees and does.
"""

import json
import time
from pathlib import Path
from openai import OpenAI

client = OpenAI()

LOG = Path("/opt/toknnews/data/analytics/gpt_diagnostics.log")


def log(msg):
    LOG.write_text(LOG.read_text() + msg + "\n" if LOG.exists() else msg + "\n")
    print(msg)


# ------------------------------------------------------------
# FILTER STORIES
# ------------------------------------------------------------
def filter_stories(stories):
    clean = []
    for s in stories:
        h = s.get("headline", "")
        summary = s.get("summary", "")

        if h.startswith("Trending on CoinGecko"):
            continue
        if len(summary) < 120:
            continue

        clean.append(s)
    return clean


# ------------------------------------------------------------
# BUILD STRUCTURED CLUSTERS
# ------------------------------------------------------------
def build_structured(stories, onchain):
    clusters = {}
    for s in stories:
        dom = s.get("domain", "general")
        clusters.setdefault(dom, {"domain": dom, "stories": []})
        clusters[dom]["stories"].append(s)
    return {"structured_clusters": clusters, "onchain": onchain}


# ------------------------------------------------------------
# GPT CALL WITH FULL DIAGNOSTICS
# ------------------------------------------------------------
def call_gpt(structured):
    prompt = f"""
You are a crypto narrative intelligence analyst.
Convert clustered crypto stories into narrative clusters.

INPUT JSON:
{json.dumps(structured, indent=2)}

OUTPUT JSON ONLY:
{{
  "clusters": [
    {{
      "name": "title",
      "summary": "1 sentence",
      "reasons": ["one", "two"],
      "stories": ["headline1", "headline2"]
    }}
  ],
  "source": "gpt"
}}
"""

    log("\n=== GPT CALL START ===")
    log("Time: " + time.strftime("%Y-%m-%d %H:%M:%S"))
    log("Structured input preview:")
    log(json.dumps(structured, indent=2)[:2000])

    try:
        response = client.responses.create(
            model="gpt-4o-mini",
            input=prompt,
            max_output_tokens=1400,
        )

        raw = response.output_text
        log("\n=== RAW GPT OUTPUT ===")
        log(raw)

        parsed = json.loads(raw)
        parsed["source"] = "gpt"
        return parsed

    except Exception as e:
        log("\n=== GPT ERROR ===")
        log(str(e))
        return {"clusters": [], "source": "gpt_failure", "error": str(e)}


# ------------------------------------------------------------
# PUBLIC ENTRYPOINT
# ------------------------------------------------------------
def generate_clusters(stories, onchain=None):
    onchain = onchain or {}

    log("\n======= NEW CLUSTER RUN =======")
    log(f"Incoming stories: {len(stories)}")

    filtered = filter_stories(stories)
    log(f"Filtered stories: {len(filtered)}")

    if len(filtered) < 4:
        log("Too little data → skipping GPT")
        return {"clusters": [], "source": "too_little_data", "ts": time.time()}

    structured = build_structured(filtered, onchain)
    res = call_gpt(structured)

    res["ts"] = time.time()
    log("Final result:")
    log(json.dumps(res, indent=2))

    return res


