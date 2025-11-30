import json, os
from datetime import datetime, timezone

base = "/var/www/toknnews/data"

# Load raw scene data
with open(os.path.join(base, "scenes.json")) as f:
    data = json.load(f)

# --- Aggregate by whole day, output as MM/DD/YY ---
daily_counts = {}

# --- Eastern-time aware day grouping ---
try:
    from zoneinfo import ZoneInfo          # Python 3.9+
except ImportError:
    from backports.zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

for s in data.get("scenes", []):
    t = str(s.get("time") or s.get("date") or "").strip()
    if not t:
        continue

    dt = None
    # --- Parse both ISO and short formats ---
    try:
        if "T" in t:
            dt = datetime.fromisoformat(t.replace("Z", ""))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        elif "/" in t:
            month, day = map(int, t.split()[0].split("/"))
            year = datetime.now(ET).year
            dt = datetime(year, month, day, tzinfo=ET)
    except Exception:
        dt = None
    if not dt:
        continue

    # --- Convert to Eastern Time and use that date key ---
    local_dt = dt.astimezone(ET)
    key = local_dt.strftime("%m/%d/%y")
    daily_counts[key] = daily_counts.get(key, 0) + int(s.get("count", 1))

# --- Write output ---
index = {
    "generated_at": datetime.utcnow().isoformat(),
    "counts": daily_counts
}

with open(os.path.join(base, "scenes_index.json"), "w") as f:
    json.dump(index, f, indent=2)

print("✅ scenes_index.json rebuilt (MM/DD/YY).")
