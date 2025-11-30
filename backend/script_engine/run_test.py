#!/usr/bin/env python3
"""
run_test.py — Test runner for script_engine_v3 and timeline_builder
"""

import json
import sys
from script_engine.persona.timeline_builder import build_timeline
from script_engine.script_engine_v3 import generate_script

def main(payload_path):
    # Load the test payload JSON
    with open(payload_path) as f:
        payload = json.load(f)

    scene_id = payload.get("scene_id", "test_scene")
    headline = payload["headline"]
    summary = payload["summary"]
    anchors = payload["anchors"]
    tone = payload.get("tone", "neutral")
    escalation_level = payload.get("escalation_level", 0)

    # Build the timeline
    timeline = build_timeline(
        character="chip",
        headline=headline,
        synthesis=summary,
        article_context=summary,
        anchors=anchors,
        allow_bitsy=True,
        allow_vega=True,
        show_intro=False,
        segment_type="headline"
    )
    # Generate the script package
    script_package = generate_script(scene_id, timeline)

    # Print output JSON
    print(json.dumps(script_package, indent=2))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 -m script_engine.run_test <payload.json>")
        sys.exit(1)
    main(sys.argv[1])

