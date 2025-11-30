#!/usr/bin/env python3
"""
grok_client.py — single source of truth for all Grok calls in Token News
All grok_writer calls will be replaced with imports from here
"""

import os
import requests
import json
from script_engine.utils import log

GROK_API_KEY = os.getenv("GROK_API_KEY")  # set this in your .env or PM2 ecosystem
GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"

def query_grok(
    prompt: str,
    temperature: float = 0.78,
    max_tokens: int = 120,
    model: str = "grok-4"
) -> str:
    """
    One-liner Grok call used by every anchor line
    """
    if not GROK_API_KEY:
        log("[GROK] DRY-RUN MODE — no API key, returning mock")
        return prompt.split("\n")[-1] + " — Grok would have said this."

    headers = {
        "Authorization": f"Bearer {GROK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": temperature,
        "max_tokens": max_tokens
    }

    try:
        r = requests.post(GROK_ENDPOINT, headers=headers, json=payload, timeout=15)
        r.raise_for_status()
        response = r.json()
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        log(f"[GROK ERROR] {e}")
        return f"[Grok offline — fallback line]"
