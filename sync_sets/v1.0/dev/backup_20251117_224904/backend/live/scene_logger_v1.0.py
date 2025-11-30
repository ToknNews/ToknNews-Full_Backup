#!/usr/bin/env python3
"""
ToknNews Scene Logger v1.0
Logs every generated scene with metadata for analytics & dashboards.
"""

import json, os, uuid, datetime

# === CONFIG ===
LOG_DIR = os.path.join(os.path.expanduser("~/Projects/toknnews-system/data"))
LOG_FILE = os.path.join(LOG_DIR, "scene_log.json")

os.makedirs(LOG_DIR, exist_ok=True)

def log_scene(character:str, topic:str, runtime:int, status:str="rendered"):
    """Append a new scene entry to the JSON log."""
    entry = {
        "scene_id": str(uuid.uuid4()),
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "character": character,
        "topic": topic,
        "runtime_sec": runtime,
        "status": status
    }

    # Load existing log or start a new one
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []
    else:
        data = []

    data.append(entry)

    # Write updated log
    with open(LOG_FILE, "w") as f:
        json.dump(data, f, indent=2)

    print(f"✅ Logged scene → {entry['scene_id']} | {character} | {topic}")

# === Example Test ===
if __name__ == "__main__":
    # Demo entry (remove later when integrated)
    log_scene(character="Chip", topic="BTC hits new ATH", runtime=25)

