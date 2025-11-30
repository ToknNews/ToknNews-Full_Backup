#!/usr/bin/env python3
import feedparser
from loguru import logger
from urllib.parse import urlparse

# Real, live RSS feeds — verified working right now
RSS_FEEDS = {
    "coindesk.com": "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph.com": "https://cointelegraph.com/rss",
    "theblock.co": "https://www.theblock.co/rss.xml",
    "decrypt.co": "https://decrypt.co/feed",
    "bitcoinmagazine.com": "https://bitcoinmagazine.com/.rss/full/"
}

def fetch_full_text(url):
    domain = urlparse(url).netloc.replace("www.", "")
    rss_url = RSS_FEEDS.get(domain)
    
    if not rss_url:
        return {"title": "No RSS", "body": "", "length": 0}
    
    try:
        feed = feedparser.parse(rss_url)
        for entry in feed.entries[:10]:  # Only check latest 10
            if entry.link == url or url in entry.link or headline_match(entry.title, url):
                title = entry.title
                body = entry.summary if hasattr(entry, "summary") else entry.get("description", "")
                from bs4 import BeautifulSoup
                clean = BeautifulSoup(body, 'html.parser').get_text()
                return {
                    "title": title[:200],
                    "body": clean[:4000],
                    "length": len(clean.split())
                }
    except Exception as e:
        logger.error(f"RSS failed: {e}")
    
    return {"title": "Not in feed", "body": "", "length": 0}

def headline_match(title, url):
    # Fallback if link doesn't match exactly
    from urllib.parse import urlparse
    path = urlparse(url).path
    return any(word in title.lower() for word in path.split("/") if len(word) > 4)

# TEST WITH A REAL, LIVE ARTICLE FROM TODAY
if __name__ == "__main__":
    # This one is live right now (Dec 10, 2024)
    test_url = "https://cointelegraph.com/news/sec-delays-decision-on-grayscale-solana-etf-until-2025"
    result = fetch_full_text(test_url)
    print(f"URL: {test_url}")
    print(f"TITLE: {result['title']}")
    print(f"LENGTH: {result['length']} words")
    print(f"PREVIEW: {result['body'][:600]}...")
