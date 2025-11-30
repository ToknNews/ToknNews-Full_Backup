#!/usr/bin/env python3
"""
ToknNews Reddit Monitor
Fetches the top posts from r/CryptoCurrency once a minute
and logs cultural/sentiment data for Shorty training.
"""

import requests
import time
import json
import os
import datetime
from update_heartbeat import update_field

# --- Reddit endpoint and headers ---
URL = "https://old.reddit.com/r/CryptoCurrency/hot.json?limit=5"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:110.0) Gecko/20100101 Firefox/110.0",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://old.reddit.com/",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}


def check_reddit():
    start = time.time()
    try:
        r = requests.get(URL, headers=HEADERS, timeout=10)
        print(f"[Reddit] Status: {r.status_code}")
        latency = int((time.time() - start) * 1000)

        if r.ok and "data" in r.text:
            data = r.json()
            update_field("reddit", "ok")
            update_field("reddit_latency_ms", latency)

            posts = data.get("data", {}).get("children", [])
            for post in posts[:3]:
                title = post.get("data", {}).get("title", "")
                if not title:
                    continue

                print(f"🪶 Logging Reddit sentiment for: {title}")

                # --- Log Reddit post for sentiment / culture analysis ---
                sentiment_entry = {
                    "title": title,
                    "subreddit": post.get("data", {}).get("subreddit", "CryptoCurrency"),
                    "timestamp": datetime.datetime.utcnow().isoformat(),
                    "upvotes": post.get("data", {}).get("ups", 0),
                    "comments": post.get("data", {}).get("num_comments", 0),
                    "url": post.get("data", {}).get("url", ""),
                    "sentiment": "unrated"
                }

                out_path = "/var/www/toknnews/data/reddit_sentiment.json"
                os.makedirs(os.path.dirname(out_path), exist_ok=True)

                try:
                    with open(out_path, "a") as f:
                        json.dump(sentiment_entry, f)
                        f.write(",\n")
                    print(f"[Reddit] 💬 Logged sentiment post: {title[:80]}")
                except Exception as e:
                    print(f"[Reddit] ⚠️ Failed to log Reddit sentiment: {e}")
        else:
            update_field("reddit", "fail")
            print(f"[Reddit] ⚠️ Request failed — status {r.status_code}")
    except Exception as e:
        update_field("reddit", "fail")
        print(f"[Reddit] ❌ Reddit error: {e}")


if __name__ == "__main__":
    while True:
        check_reddit()
        time.sleep(60)

