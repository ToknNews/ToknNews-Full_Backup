#!/usr/bin/env python3
import os, json, glob, datetime

SCENES_DIR = "/var/www/toknnews/data/scenes"
OUT_PATH   = "/var/www/toknnews/data/scenes.json"

def current_data():
    if not os.path.exists(OUT_PATH):
        return {"generated_at": None, "scenes": [], "daily_counts": []}
    with open(OUT_PATH) as f:
        try: return json.load(f)
        except Exception: return {"generated_at": None, "scenes": [], "daily_counts": []}

def main():
    data = current_data()
    existing_times = {s.get("time") for s in data.get("scenes", []) if s.get("time")}

    # Scan for new scene files
    files = sorted(glob.glob(os.path.join(SCENES_DIR, "*.json")))
    new_scenes = []
    for path in files:
        with open(path) as f:
            s = json.load(f)
        t = s.get("timestamp") or s.get("time")
        if t and t not in existing_times:
            new_scenes.append({
                "time": t,
                "character": s.get("character", "Chip"),
                "topic": s.get("headline") or s.get("title") or "—",
                "runtime": s.get("runtime_s", 15)
            })

    if not new_scenes:
        return

    # Append new scenes
    data["scenes"].extend(new_scenes)

    # Recompute daily counts
    daily = {}
    for s in data["scenes"]:
        date = (s.get("time") or "")[:10]
        if date: daily[date] = daily.get(date, 0) + 1
    data["daily_counts"] = [{"date": d, "count": daily[d]} for d in sorted(daily)]

    data["generated_at"] = datetime.datetime.utcnow().isoformat()

    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    main()
