#!/usr/bin/env python3
# =========================================================
# TOKNNews RSS Ingestor (Merge Mode)
# Adds new items from verified external feeds into the
# existing /data/raw/rss_latest.json used by the compiler.
# =========================================================
import feedparser, json, os, hashlib, datetime, sys

ROOT = "/var/www/toknnews"
DATA = os.path.join(ROOT, "data")
RAW_PATH = os.path.join(DATA, "raw")
SOURCE_LIST = os.path.join(DATA, "rss_source_list.json")
OUT_PATH = os.path.join(RAW_PATH, "rss_latest.json")

os.makedirs(RAW_PATH, exist_ok=True)

def normalize_item(entry, source_name):
    title = (entry.get("title") or "").strip()
    link = (entry.get("link") or "").strip()
    if not title or not link:
        return None
    desc = (entry.get("summary") or "").strip()
    pub  = entry.get("published") or entry.get("updated") or ""
    uid  = hashlib.md5((title + link).encode("utf-8")).hexdigest()
    return {
        "id": uid,
        "headline": title,
        "source": source_name,
        "url": link,
        "description": desc,
        "published": pub
    }

def load_existing():
    if not os.path.isfile(OUT_PATH):
        return []
    try:
        data = json.load(open(OUT_PATH, "r", encoding="utf-8"))
        return data.get("items", [])
    except Exception:
        return []

def main():
    if not os.path.isfile(SOURCE_LIST):
        print(f"[RSS] ❌ Missing {SOURCE_LIST}", file=sys.stderr)
        sys.exit(1)

    try:
        feeds = json.load(open(SOURCE_LIST, "r", encoding="utf-8"))
    except Exception as e:
        print(f"[RSS] ❌ Failed to read source list: {e}", file=sys.stderr)
        sys.exit(1)

    existing = {i["id"]: i for i in load_existing()}
    added = 0

    for url in feeds:
        try:
            feed = feedparser.parse(url)
            src = (feed.feed.get("title") or url.split("/")[2]).strip()
            for e in feed.entries[:50]:
                item = normalize_item(e, src)
                if item and item["id"] not in existing:
                    existing[item["id"]] = item
                    added += 1
            print(f"[RSS] ✅ {src}: +{min(len(feed.entries),50)} checked")
        except Exception as e:
            print(f"[RSS] ⚠️ {url} failed: {e}", file=sys.stderr)

    items = list(existing.values())
    items.sort(key=lambda x: x.get("published",""), reverse=True)

    payload = {"generated_at": datetime.datetime.utcnow().isoformat(),
               "items": items}

    tmp = OUT_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    json.load(open(tmp, "r", encoding="utf-8"))  # validation
    os.replace(tmp, OUT_PATH)
    print(f"[RSS] ✅ merged {added} new → total {len(items)} → {OUT_PATH}")

if __name__ == "__main__":
    main()
