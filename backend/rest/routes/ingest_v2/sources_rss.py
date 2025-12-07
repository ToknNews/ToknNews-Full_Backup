#!/usr/bin/env python3
"""
sources_rss.py
ToknNews 2025 — Canonical RSS Fetcher (Transfer Brain v1.0)

Responsible for collecting RSS headlines from the following sources:
 - CoinDesk
 - CoinTelegraph
 - The Block
 - Decrypt
 - CryptoPanic RSS

Output: list of raw dicts for normalization:
{
    "headline": <str>,
    "source": "RSS",
    "timestamp": <epoch>
}
"""

import time
import traceback
import feedparser


# ---------------------------------------------------------------
# RSS SOURCE DEFINITIONS
# ---------------------------------------------------------------

RSS_FEEDS = {
    "coindesk":      "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "cointelegraph": "https://cointelegraph.com/rss",
    "decrypt":       "https://decrypt.co/feed",
    "theblock":      "https://www.theblock.co/rss",
    "cryptopanic":   "https://cryptopanic.com/feed/"
}


# ---------------------------------------------------------------
# SINGLE FEED FETCHER
# ---------------------------------------------------------------

def _fetch_feed(url, label):
    results = []

    try:
        parsed = feedparser.parse(url)
        entries = parsed.get("entries", [])
    except Exception:
        print(f"[RSS] ERROR fetching {label}:")
        traceback.print_exc()
        return results

    for e in entries:
        title = (
            e.get("title")
            or e.get("summary")
            or ""
        ).strip()

        if not title:
            continue

        results.append({
            "headline": title,
            "source": "RSS",
            "timestamp": time.time()
        })

    return results


# ---------------------------------------------------------------
# BATCH FETCHER
# ---------------------------------------------------------------

def fetch_rss_batch():
    """
    Fetch all RSS sources synchronously.
    Returns a flat list of raw RSS items.
    """

    all_items = []

    for label, url in RSS_FEEDS.items():
        try:
            items = _fetch_feed(url, label)
            print(f"[RSS] {label} → {len(items)}")
            all_items.extend(items)
        except Exception:
            print(f"[RSS] ERROR in feed: {label}")
            traceback.print_exc()

    # Deduplicate by headline text
    unique = []
    seen = set()
    for item in all_items:
        h = item["headline"]
        if h not in seen:
            seen.add(h)
            unique.append(item)

    print(f"[RSS] Total unique → {len(unique)}")
    return unique


# ---------------------------------------------------------------
# CLI ENTRY
# ---------------------------------------------------------------
if __name__ == "__main__":
    out = fetch_rss_batch()
    print(f"[RSS] Returned → {len(out)} items")
