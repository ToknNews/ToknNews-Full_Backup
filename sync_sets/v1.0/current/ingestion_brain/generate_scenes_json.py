#!/usr/bin/env python3
# =========================================================
# TOKNNews Unified Scene Compiler  v1.0
# =========================================================
# • Reads all configured feeds (JSON / RSS)
# • Compiles scenes using scene_compiler_live.compile_scene
# • Writes every scene directly into SQLite ledger (scenes table)
# • Outputs concise one-line summaries per feed
# • Ready for prompt_worker & dashboard_aggregator extensions
# =========================================================

import os, json, datetime, hashlib, uuid
from scene_compiler_live import compile_scene
from db import insert_scene

# toggle minimal logging
VERBOSE = True

# ---------------------------------------------------------
#  Universal Feed Handler
# ---------------------------------------------------------
def generate_from_feed(path, source_name="Unknown", character="chip"):
    """Reads any feed file, compiles scenes, and logs to SQLite."""
    if not os.path.exists(path):
        if VERBOSE:
            print(f"[Feed] {source_name}: missing ({path})")
        return 0

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[Feed] {source_name}: failed to read ({e})")
        return 0

    # handle {"items": [...]} wrappers
    if isinstance(data, dict) and "items" in data:
        data = data["items"]
    if not isinstance(data, list):
        if VERBOSE:
            print(f"[Feed] {source_name}: invalid format")
        return 0

    count = 0
    for item in data:
        headline = item.get("headline") or item.get("title") or ""
        source = item.get("source") or source_name
        if not headline:
            continue

        # Compile scene
        try:
            scene = compile_scene(headline=headline, source=source, character=character)
        except Exception as e:
            print(f"[Feed] {source}: compile error: {e}")
            continue

        # Insert into ledger
        try:
            insert_scene(
                str(uuid.uuid4()),
                headline,
                source,
                scene.get("sentiment", "neutral"),
                item.get("url") or item.get("link")
            )
            count += 1
        except Exception as e:
            print(f"[Feed] {source}: DB insert error: {e}")
            continue

    if VERBOSE:
        print(f"[Feed] {source_name}: {count} scenes processed")
    return count


# ---------------------------------------------------------
#  Feed configuration
# ---------------------------------------------------------
FEEDS = [
    # Core JSON feeds
    {"path": "/var/www/toknnews/data/feeds/cointelegraph_latest.json", "name": "Cointelegraph"},
    {"path": "/var/www/toknnews/data/feeds/coingecko_latest.json", "name": "CoinGecko"},
    {"path": "/var/www/toknnews/data/feeds/theblock_latest.json", "name": "The Block"},
    {"path": "/var/www/toknnews/data/feeds/coindesk_latest.json", "name": "Coindesk"},
    # Unified RSS feed (merged external + internal)
    {"path": "/var/www/toknnews/data/raw/rss_latest.json", "name": "RSS"},
    # Market & token data
    {"path": "/var/www/toknnews/data/raw/moralis_latest.json", "name": "Moralis"},
    {"path": "/var/www/toknnews/data/raw/api_filtered.json", "name": "DexScreener"},
    # Future social sentiment sources
    {"path": "/var/www/toknnews/data/raw/reddit_latest.json", "name": "Reddit"},
    {"path": "/var/www/toknnews/data/raw/cryptopanic_latest.json", "name": "CryptoPanic"}
]


# ---------------------------------------------------------
#  Main execution
# ---------------------------------------------------------
if __name__ == "__main__":
    total = 0
    start = datetime.datetime.utcnow()
    for feed in FEEDS:
        total += generate_from_feed(feed["path"], feed["name"])
    elapsed = (datetime.datetime.utcnow() - start).total_seconds()
    print(f"--- Compilation complete: {total} scenes in {elapsed:.2f}s ---")

    # placeholders for next modules
    # from prompt_worker import run_prompt_enrichment
    # from dashboard_aggregator import update_dashboard
