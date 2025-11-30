#!/usr/bin/env python3
"""
Script-only ToknNews episode test.
No audio rendering.
No ElevenLabs calls.
Just prints the full show script in order.
"""

import json
from script_engine.knowledge.episode_builder import build_episode
from script_engine.persona.timeline_builder import build_timeline

print("\n=========== TOKNNEWS — EPISODE SCRIPT TEST (NO AUDIO) ===========\n")

episode = build_episode()

if "error" in episode:
    print("ERROR: No stories available.")
    exit(1)

story_clusters = episode["rundown"]
episode_id = episode["episode_id"]

print(f"Episode ID: {episode_id}")
print(f"Stories in Rundown: {len(story_clusters)}\n")


# Build timeline
timeline = build_timeline(
    story_clusters,
    daypart="evening",
    show_mode="NEWS"
)

blocks = timeline["blocks"]

# Pretty print the full script
for i, block in enumerate(blocks):
    speaker = block["speaker"].upper()
    tag = block.get("tag", "line")
    text = block["text"]

    print(f"\n--- BLOCK {i} | {speaker} | {tag} ---")
    print(text)

print("\n=========== END OF SCRIPT ===========\n")
