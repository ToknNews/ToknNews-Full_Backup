#!/usr/bin/env python3

import os
import requests

# Example for Twitter/X (requires API credentials)
# DO NOT hardcode secrets here

TWITTER_API_URL = "https://api.twitter.com/2/tweets"
TWITTER_BEARER = os.getenv("TWITTER_BEARER_TOKEN")


def post_to_x(text: str):
    if not TWITTER_BEARER:
        return {"ok": False, "error": "Missing Twitter token"}

    headers = {
        "Authorization": f"Bearer {TWITTER_BEARER}",
        "Content-Type": "application/json"
    }

    payload = {"text": text}

    r = requests.post(TWITTER_API_URL, headers=headers, json=payload)

    try:
        return r.json()
    except Exception:
        return {"ok": False, "error": "Invalid response"}
