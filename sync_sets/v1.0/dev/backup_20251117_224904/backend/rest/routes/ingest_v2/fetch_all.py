from fastapi import APIRouter
import requests
import feedparser
import json
import time
import hashlib

router = APIRouter(prefix="/ingest/v2")

def make_id(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]

RSS_FEEDS = [
    "https://www.coindesk.com/arc/outboundfeeds/rss/?outputType=xml",
    "https://cointelegraph.com/rss",
]

def fetch_rss():
    items = []
    for url in RSS_FEEDS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            headline = entry.get("title", "").strip()
            link = entry.get("link", "")
            if not headline:
                continue
            items.append({
                "id": make_id(headline + link),
                "headline": headline,
                "url": link,
                "source": "rss",
                "ts": time.time()
            })
    return items

def fetch_coindesk():
    try:
        r = requests.get("https://api.coindesk.com/v1/articles/latest")
        return [
            {
                "id": make_id(a["title"]),
                "headline": a["title"],
                "url": a.get("url", ""),
                "source": "coindesk",
                "ts": time.time()
            }
            for a in r.json().get("articles", [])
        ]
    except:
        return []

@router.get("/fetch_all")
def fetch_all():
    results = []
    results.extend(fetch_rss())
    results.extend(fetch_coindesk())
    return {"count": len(results), "items": results}
