#!/usr/bin/env python3
"""
TOKNNews Hybrid Ingestor
Unifies RSS, API, and Reddit sources into one deduped, normalized feed.
Writes /data/raw/rss_latest.json and updates heartbeat.
"""

import os, json, time, hashlib, requests, feedparser
from datetime import datetime
from heartbeat_updater import update_heartbeat

DATA_DIR = "/var/www/toknnews/data"
REGISTRY_PATH = os.path.join(DATA_DIR, "feed_registry.json")
OUTPUT_PATH = os.path.join(DATA_DIR, "raw/rss_latest.json")
INGEST_LOG = os.path.join(DATA_DIR, "ingest_log.jsonl")

# ------------------------------------------------------------
# Utility helpers
# ------------------------------------------------------------
def load_registry():
    if os.path.exists(REGISTRY_PATH):
        try:
            with open(REGISTRY_PATH, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Registry] Error reading registry: {e}")
    return {"rss": [], "api": [], "reddit": []}

def dedupe(items, memory_limit=300):
    """
    Deduplicate items by title + source + link and filter out old timestamps.
    Keeps only recent unique items (within 48h).
    """
    from datetime import datetime, timedelta

    seen = set()
    unique = []
    cutoff = datetime.utcnow() - timedelta(hours=48)

    for i in reversed(items):  # newest first
        # --- Build a strong uniqueness key ---
        key = (
            i.get("title", "").strip(),
            i.get("source", "").strip(),
            i.get("link", "").strip()
        )

        # --- Skip if duplicate ---
        if key in seen:
            continue

        # --- Skip if older than cutoff ---
        ts = i.get("timestamp", "")
        try:
            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
            if dt < cutoff:
                continue
        except Exception:
            pass

        unique.append(i)
        seen.add(key)

        if len(unique) >= memory_limit:
            break

    unique.reverse()
    return unique

def timestamp_now():
    return datetime.utcnow().isoformat() + "Z"

def safe_get(url):
    try:
        r = requests.get(url, timeout=10, headers={"User-Agent": "ToknNewsBot/1.0"})
        if r.status_code == 200:
            return r.text
        else:
            print(f"[Fetch] {url} returned {r.status_code}")
    except Exception as e:
        print(f"[Fetch] Error fetching {url}: {e}")
    return None

# ------------------------------------------------------------
# Source handlers
# ------------------------------------------------------------
def fetch_rss(url):
    parsed = feedparser.parse(url)
    items = []
    for entry in parsed.entries[:20]:
        items.append({
            "title": entry.get("title", "").strip(),
            "summary": entry.get("summary", "")[:300],
            "source": parsed.feed.get("title", url),
            "link": entry.get("link", ""),
            "timestamp": timestamp_now()
        })
    return items

def fetch_api(url):
    try:
        data = requests.get(url, timeout=10).json()
        if isinstance(data, dict) and "posts" in data:
            posts = data["posts"]
        elif isinstance(data, list):
            posts = data
        else:
            posts = [data]
        items = []
        for p in posts[:20]:
            title = str(p.get("title") or p.get("description") or "Untitled")
            summary = p.get("body") or p.get("summary") or ""
            items.append({
                "title": title.strip(),
                "summary": summary[:300],
                "source": url.split("//")[-1].split("/")[0],
                "link": p.get("url", ""),
                "timestamp": timestamp_now()
            })
        return items
    except Exception as e:
        print(f"[API] {url} error: {e}")
        return []

def fetch_reddit(url):
    try:
        data = requests.get(url, headers={"User-Agent": "ToknNewsBot/1.0"}, timeout=10).json()
        items = []
        for p in data["data"]["children"]:
            post = p["data"]
            items.append({
                "title": post.get("title", ""),
                "summary": post.get("selftext", "")[:300],
                "source": "reddit",
                "link": "https://reddit.com" + post.get("permalink", ""),
                "timestamp": timestamp_now()
            })
        return items
    except Exception as e:
        print(f"[Reddit] {url} error: {e}")
        return []

# ------------------------------------------------------------
# Main ingestion orchestrator
# ------------------------------------------------------------
def ingest_all():
    registry = load_registry()

    # --- Build combined news feed (RSS + API) ---
    all_items = []

    # Primary RSS sources
    for url in registry.get("rss", []):
        all_items += fetch_rss(url)

    # API sources (Coindesk, CryptoPanic, etc.)
    for url in registry.get("api", []):
        all_items += fetch_api(url)

    # --- Reddit ingestion (sentiment training only; not merged) ---
    reddit_items = []
    for url in registry.get("reddit", []):
        reddit_items += fetch_reddit(url)

    # --- Reddit ingestion (separate channel for sentiment training) ---
    reddit_items = []
    for url in registry.get("reddit", []):
        reddit_items += fetch_reddit(url)

    if reddit_items:
        reddit_output = {
            "generated_at": timestamp_now(),
            "count": len(reddit_items),
            "items": reddit_items
        }
        reddit_path = os.path.join(DATA_DIR, "raw/reddit_training_feed.json")
        tmp_reddit = reddit_path + ".tmp"
        os.makedirs(os.path.dirname(reddit_path), exist_ok=True)
        with open(tmp_reddit, "w") as f:
            json.dump(reddit_output, f, indent=2)
        os.replace(tmp_reddit, reddit_path)
        print(f"[HybridIngest] 🧠 Saved {len(reddit_items)} Reddit posts for sentiment training.")

    all_items = [i for i in all_items if i.get("title")]
    deduped = dedupe(all_items)
    output = {
        "generated_at": timestamp_now(),
        "count": len(deduped),
        "items": deduped
    }

    # === Merge daily_counts.json (preserve history) ===
    """
    from collections import Counter

    daily_counts_path = os.path.join(DATA_DIR, "daily_counts.json")
    existing_counts = {}

    # 1️⃣ Load existing file if it exists
    if os.path.exists(daily_counts_path):
        try:
            with open(daily_counts_path, "r") as f:
                existing_counts = json.load(f)
        except Exception:
            existing_counts = {}

    # 2️⃣ Count today’s items
    new_counts = Counter()
    for i in all_items:
        if "timestamp" in i:
            day = i["timestamp"].split("T")[0]
            new_counts[day] += 1

    # 3️⃣ Replace today's counts (no cumulative inflation)
    for day, count in new_counts.items():
        existing_counts[day] = count

    # 4️⃣ Write back atomically
    tmp_path = daily_counts_path + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(dict(sorted(existing_counts.items())), f, indent=2)
    os.replace(tmp_path, daily_counts_path)

    print(f"[Dashboard] ✅ Merged daily_counts.json ({len(existing_counts)} total days)")
    """
    # Atomic write
    tmp_path = OUTPUT_PATH + ".tmp"
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(tmp_path, "w") as f:
        json.dump(output, f, indent=2)
    os.replace(tmp_path, OUTPUT_PATH)

    # Log + heartbeat
    entry = {
        "timestamp": timestamp_now(),
        "total_sources": sum(len(v) for v in registry.values()),
        "total_items": len(deduped)
    }
    with open(INGEST_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

    update_heartbeat("Hybrid Ingest", "neutral", 0, "success")
    print(f"[HybridIngest] ✅ Combined {len(deduped)} unique items from {entry['total_sources']} sources.")

    return output

if __name__ == "__main__":
    result = ingest_all()
    # === Trigger scene compiler to refresh dashboard ===
    try:
        import subprocess
        print("[System] 🧩 Running scene compiler to update snapshot...")
        subprocess.run(
            ["python3", "/var/www/toknnews/modules/scene_compiler_live.py"],
            check=True
        )
    except Exception as e:
        print(f"[System] ⚠️ Could not run compiler: {e}")
