# x_event_fetcher.py
"""
ToknNews — X Event Fetcher (RAW INGESTION)

Pulls factual, high-signal posts from X search.
No sentiment. No editorial logic. No dedupe.
"""

import os
import requests
from datetime import datetime, timedelta

X_BEARER_TOKEN = os.getenv("X_BEARER_TOKEN")
SEARCH_URL = "https://api.twitter.com/2/tweets/search/recent"

LOOKBACK_HOURS = 12
MAX_RESULTS = 20

QUERY = (
    '(announced OR launch OR approved OR halted OR exploited OR '
    'transferred OR acquired OR filed OR suspended OR upgraded) '
    'filter:verified -is:reply'
)

def _headers():
    return {
        "Authorization": f"Bearer {X_BEARER_TOKEN}",
        "Content-Type": "application/json"
    }

def fetch_x_events():
    """
    Fetch high-signal factual posts from X.

    Returns:
        list[dict]: raw tweet objects from X API
    """
    if not X_BEARER_TOKEN:
        raise RuntimeError("X_BEARER_TOKEN not set in environment")

    start_time = (
        datetime.utcnow() - timedelta(hours=LOOKBACK_HOURS)
    ).isoformat(timespec="seconds") + "Z"

    params = {
        "query": QUERY,
        "start_time": start_time,
        "max_results": MAX_RESULTS,
        "tweet.fields": "created_at,public_metrics",
    }

    resp = requests.get(
        SEARCH_URL,
        headers=_headers(),
        params=params,
        timeout=15
    )

    if resp.status_code != 200:
        raise RuntimeError(f"X API error {resp.status_code}: {resp.text}")

    posts = resp.json().get("data", [])

    # Engagement floor to reduce noise
    return [
        p for p in posts
        if p.get("public_metrics", {}).get("like_count", 0) >= 3
        or p.get("public_metrics", {}).get("retweet_count", 0) >= 1
    ]
