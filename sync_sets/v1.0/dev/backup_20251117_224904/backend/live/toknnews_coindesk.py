#!/usr/bin/env python3
"""
ToknNews Multi-Source RSS Ingestor
Combines multiple free RSS feeds into one JSON file and updates heartbeat.json
"""

import feedparser, json, time
from datetime import datetime
from update_heartbeat import update_field

RSS_FEEDS = {
    "CoinDesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "CoinTelegraph": "https://cointelegraph.com/rss",
    "CryptoNews": "https://cryptonews.com/news/feed",
    "Decrypt": "https://decrypt.co/feed",
    "YahooFinance": "https://finance.yahoo.com/news/rssindex",
    "GoogleNews": "https://news.google.com/rss/search?q=crypto+OR+bitcoin+OR+ethereum"
}

OUTFILE = "/var/www/toknnews/data/raw/rss_latest.json"

def fetch_feeds():
    start = time.time()
    all_items = []

    for name, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                for entry in feed.entries[:10]:
                    all_items.append({
                        "source": name,
                        "title": entry.get("title", ""),
                        "url": entry.get("link", ""),
                        "published": entry.get("published", ""),
                        "summary": entry.get("summary", "")[:400]
                    })
                update_field(f"{name.lower()}_rss", "ok")
            else:
                update_field(f"{name.lower()}_rss", "empty")
        except Exception as e:
            update_field(f"{name.lower()}_rss", "fail")
            print(f"[{name}] error: {e}")

    latency = int((time.time() - start) * 1000)
    update_field("rss_latency_ms", latency)

    with open(OUTFILE, "w") as f:
        json.dump(all_items, f, indent=2)

    print(f"[ToknNews RSS] {len(all_items)} items written → {OUTFILE}")

if __name__ == "__main__":
    while True:
        fetch_feeds()
        time.sleep(300)  # every 5 minutes
