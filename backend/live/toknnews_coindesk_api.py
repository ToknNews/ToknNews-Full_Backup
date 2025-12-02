#!/usr/bin/env python3
"""
ToknNews CoinDesk API Fetcher
Fetches latest CoinDesk articles via official API and caches enriched data.
"""
import os
import json
import requests
from datetime import datetime

# Load API key from environment (ensure it's set in Vault/ENV)
COINDESK_API_KEY = os.getenv("COINDESK_API_KEY", "").strip()
if not COINDESK_API_KEY:
    raise RuntimeError("COINDESK_API_KEY is not set in environment")

# API endpoint and parameters
API_URL = "https://data-api.coindesk.com/news/v1/article/list"
PARAMS = {
    "lang": "EN",
    "limit": "10",
    "api_key": COINDESK_API_KEY
}
HEADERS = {"Accept": "application/json"}

# Output directory and file name (with date for caching)
DATA_DIR = "/opt/toknnews/data/sources"
os.makedirs(DATA_DIR, exist_ok=True)
date_str = datetime.utcnow().strftime("%Y%m%d")
OUTFILE = os.path.join(DATA_DIR, f"coindesk_{date_str}.json")

def fetch_coindesk_articles():
    """Fetch latest CoinDesk articles and save enriched metadata."""
    try:
        resp = requests.get(API_URL, params=PARAMS, headers=HEADERS, timeout=10)
    except requests.RequestException as e:
        print(f"[CoinDesk] Request error: {e}")
        return False

    if resp.status_code != 200:
        print(f"[CoinDesk] API error {resp.status_code}: {resp.text[:200]}")
        return False

    data = resp.json()
    # The API returns articles under 'Data' or 'articles' key:
    articles = data.get("Data") or data.get("articles") or []
    if not articles:
        print("[CoinDesk] No articles in response.")
        return False

    results = []
    for article in articles:
        title = article.get("TITLE") or article.get("title", "")
        body = article.get("BODY") or article.get("body", "")
        author = article.get("AUTHORS") or article.get("author", "")
        # Convert published timestamp to ISO format (assuming PUBLISHED_ON is UNIX epoch in seconds)
        ts = article.get("PUBLISHED_ON") or article.get("published_on") or article.get("published") 
        if ts:
            try:
                # Some APIs return timestamp as int (seconds); if string, try int conversion
                ts_val = int(ts) if isinstance(ts, str) else ts
                published_iso = datetime.utcfromtimestamp(ts_val).isoformat() + "Z"
            except Exception:
                # Fallback if already an ISO string
                published_iso = str(ts)
        else:
            published_iso = ""
        url = article.get("URL") or article.get("url", "")
        image = article.get("IMAGEURL") or article.get("imageurl") or article.get("image", "")
        results.append({
            "title": title.strip(),
            "url": url.strip(),
            "body": body.strip(),
            "author": author.strip(),
            "published": published_iso,
            "image_url": image.strip()
        })

    # Prepare output JSON structure
    output = {
        "source": "CoinDesk",
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "articles": results
    }
    # Write to file (atomic write via temp file for safety)
    tmp_path = OUTFILE + ".tmp"
    with open(tmp_path, "w") as f:
        json.dump(output, f, indent=2)
    os.replace(tmp_path, OUTFILE)
    print(f"[CoinDesk] ✅ Fetched {len(results)} articles and saved to {OUTFILE}")
    return True

if __name__ == "__main__":
    fetch_coindesk_articles()
