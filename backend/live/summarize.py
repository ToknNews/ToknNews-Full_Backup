import json
from datetime import datetime

INPUT = f"/opt/toknnews/data/merged/merged_{datetime.utcnow().strftime('%Y%m%d')}.json"
OUTPUT = "/opt/toknnews/data/final/summary.json"

def summarize():
    summary = []
    try:
        with open(INPUT) as f:
            merged = json.load(f)

        for source in merged.get("data", []):
            for key, items in source.items():
                if isinstance(items, dict):
                    items = [items]
                for item in items:
                    text = ""
                    if isinstance(item, dict):
                        text = item.get("text") or item.get("title") or json.dumps(item)[:200]
                    elif isinstance(item, str):
                        text = item
                    summary.append(f"[{key}] {text[:280]}")  # Trim to tweet size

        with open(OUTPUT, "w") as out:
            json.dump({"summary": summary, "generated_at": datetime.utcnow().isoformat()}, out, indent=2)

        print(f"[Summarize] ✅ Wrote {len(summary)} entries → {OUTPUT}")

    except Exception as e:
        print(f"[Summarize] ❌ Failed: {e}")

if __name__ == "__main__":
    summarize()
