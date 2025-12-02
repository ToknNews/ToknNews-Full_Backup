# /opt/toknnews/backend/live/merge_sources.py

import os
import json
from datetime import datetime

SOURCE_DIR = "/opt/toknnews/data/sources"
MERGED_FILE = f"{SOURCE_DIR}/merged_sources_{datetime.now().strftime('%Y%m%d')}.json"

def load_json_files(prefix):
    data = []
    for file in sorted(os.listdir(SOURCE_DIR)):
        if file.startswith(prefix) and file.endswith(".json"):
            try:
                with open(os.path.join(SOURCE_DIR, file)) as f:
                    data.extend(json.load(f))
            except Exception as e:
                print(f"[WARN] Failed loading {file}: {e}")
    return data

def merge_all_sources():
    merged = {
        "coindesk": load_json_files("coindesk_"),
        "twitter": load_json_files("twitter_"),
        "market_intel": load_json_files("market_intel_")
    }

    with open(MERGED_FILE, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"[Merge] ✅ Wrote merged file → {MERGED_FILE}")

if __name__ == "__main__":
    merge_all_sources()
