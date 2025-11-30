#!/usr/bin/env python3
import sys
import json
import time

# Always import as a package
from script_engine.script_engine_v3 import generate_script


def main():
    # Get filename from arguments
    filename = sys.argv[1] if len(sys.argv) > 1 else "test_payload.json"

    # Load test payload
    with open(filename, "r") as f:
        payload = json.load(f)

    # Extract fields
    headline = payload.get("headline", "")
    article_context = payload.get("article_context", "")
    cluster_articles = payload.get("cluster_articles", [])

    # Generate script via engine
    script = generate_script(
        headline=headline,
        article_context=article_context,
        cluster_articles=cluster_articles,
        anchors=payload.get("anchors")
    )

    # Pretty-print output
    print(json.dumps(script, indent=2))


if __name__ == "__main__":
    main()
