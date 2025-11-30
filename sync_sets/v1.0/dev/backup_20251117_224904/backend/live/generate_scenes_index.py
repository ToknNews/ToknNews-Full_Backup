#!/usr/bin/env python3
import os, json, glob, datetime

SCENES_DIR = "/var/www/toknnews/data/scenes"
OUT_PATH   = "/var/www/toknnews/data/scenes_index.json"

def load_scene(path):
    with open(path) as f:
        d = json.load(f)
    return {
        "time": d.get("timestamp"),
        "character": (d.get("character") or "Chip").title(),
        "topic": d.get("headline") or d.get("title") or "—",
        "runtime_s": d.get("runtime_s", 15),
        "file": os.path.basename(path),
    }

def main():
    os.makedirs(SCENES_DIR, exist_ok=True)
    files = sorted(glob.glob(os.path.join(SCENES_DIR, "*.json")), reverse=True)[:50]
    items = []
    for p in files:
        try:
            items.append(load_scene(p))
        except Exception:
            items.append({"time": None, "character": "?", "topic": f"ERR {os.path.basename(p)}", "runtime_s": None})
    payload = {
        "generated_at": datetime.datetime.utcnow().isoformat(),
        "count": len(items),
        "items": items
    }
    with open(OUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)

if __name__ == "__main__":
    main()
