import json
from script_engine_v3 import generate_script  # adjust import if needed
from timeline_builder import build_timeline  # adjust import if needed

# Load test payload
with open("test_payload_full_scene.json") as f:
    payload = json.load(f)

# Generate the script for the scene
scene_id = payload["scene_id"]
headline = payload["headline"]
summary = payload["summary"]
anchors = payload["anchors"]
tone = payload["tone"]
escalation_level = payload["escalation_level"]

# Build timeline using your existing function
timeline = build_timeline(headline, summary, anchors, tone, escalation_level)

# Generate script blocks
script_package = generate_script(scene_id, timeline)

# Print result
import json
print(json.dumps(script_package, indent=2))
