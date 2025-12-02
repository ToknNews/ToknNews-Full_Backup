import os
import json
from datetime import datetime

sources = {
    "coindesk": "/opt/toknnews/data/sources/coindesk_{}.json",
    "market_intel": "/opt/toknnews/data/sources/market_intel_{}.json",
    "twitter": "/opt/toknnews/data/raw/twitter_latest.json"
}

def merge_sources(output_file):
    merged = {"timestamp": datetime.utcnow().isoformat(), "data": []}

    date_str = datetime.utcnow().strftime("%Y%m%d")

    for name, path_template in sources.items():
        path = path_template.format(date_str) if '{}' in path_template else path_template
        if os.path.exists(path):
            with open(path) as f:
                try:
                    data = json.load(f)
                    merged["data"].append({name: data})
                except Exception as e:
                    print(f"[{name}] Skipped due to error: {e}")
        else:
            print(f"[{name}] Source file missing: {path}")

    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w") as f:
        json.dump(merged, f, indent=2)

    print(f"[Merge] ✅ Merged sources into {output_file}")

if __name__ == "__main__":
    output_path = f"/opt/toknnews/data/merged/merged_{datetime.utcnow().strftime('%Y%m%d')}.json"
    merge_sources(output_path)
