#!/usr/bin/env python3

import os
import time
import json
import requests
from datetime import datetime
from dotenv import load_dotenv

from backend.runtime.sqlite_utils import connect_sqlite

# --------------------------------------------------
# LOAD ENV (DETERMINISTIC)
# --------------------------------------------------
load_dotenv(dotenv_path="/opt/toknnews/.env", override=True)

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

MARKETAUX_TOKEN = (
    os.getenv("MARKETAUX_API_KEY")
    or os.getenv("MARKETAUX_TOKEN")
)

DB_PATH = "/opt/toknnews/data/ingestion/ingestion.db"
BASE_URL = "https://api.marketaux.com/v1/news/all"

DEFAULT_PARAMS = {
    "limit": 50,
    "languages": "en",
    "must_have_entities": "true",
    "group_similar": "false",   # IMPORTANT: keep false to preserve metadata
    "countries": "us",
}

# Advisory thresholds (NOT hard requirements)
MIN_MARKETAUX_RELEVANCE = 60
MAX_FALLBACK_ITEMS = 5

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def iso_to_epoch(ts: str) -> int:
    return int(datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp())

# --------------------------------------------------
# FETCHER
# --------------------------------------------------

def fetch_marketaux_batch(symbols: str) -> list:
    if not MARKETAUX_TOKEN:
        print("[MARKETAUX] Missing API token")
        return []

    params = {
        **DEFAULT_PARAMS,
        "api_token": MARKETAUX_TOKEN,
        "symbols": symbols,
    }

    print("[MARKETAUX] Request params:")
    for k, v in params.items():
        print(f"  {k} = {v}")

    try:
        r = requests.get(BASE_URL, params=params, timeout=15)
    except Exception as e:
        print("[MARKETAUX] Request failed:", e)
        return []

    if r.status_code != 200:
        print("[MARKETAUX] HTTP error:", r.status_code)
        print("[MARKETAUX] Response body:", r.text[:500])
        return []

    payload = r.json()
    articles = payload.get("data", [])

    print(f"[MARKETAUX] API returned {len(articles)} articles")

    if not articles:
        return []

    conn = connect_sqlite(DB_PATH)
    cur = conn.cursor()

    now = int(time.time())
    out = []

    high_signal = []
    fallback_pool = []

    # --------------------------------------------------
    # CLASSIFY (SOFT)
    # --------------------------------------------------
    for a in articles:
        uuid = a.get("uuid")
        if not uuid:
            continue

        score = a.get("relevance_score")

        try:
            score = float(score) if score is not None else None
        except Exception:
            score = None

        if score is not None and score >= MIN_MARKETAUX_RELEVANCE:
            high_signal.append(a)
        else:
            fallback_pool.append(a)

    print(f"[MARKETAUX] High-signal: {len(high_signal)} | Fallback: {len(fallback_pool)}")
    print("[MARKETAUX] Sample relevance scores:",
          [a.get("relevance_score") for a in articles[:5]])

    # --------------------------------------------------
    # SELECT FINAL SET
    # --------------------------------------------------
    if high_signal:
        selected_articles = high_signal
    else:
        selected_articles = fallback_pool[:MAX_FALLBACK_ITEMS]

    print(f"[MARKETAUX] Selected {len(selected_articles)} articles")

    # --------------------------------------------------
    # INGEST
    # --------------------------------------------------
    for a in selected_articles:
        uuid = a.get("uuid")
        if not uuid:
            continue

        published_at = iso_to_epoch(a["published_at"])

        cur.execute(
            """
            INSERT OR IGNORE INTO marketaux_raw
            (uuid, raw_json, published_at, ingested_at)
            VALUES (?, ?, ?, ?)
            """,
            (
                uuid,
                json.dumps(a),
                published_at,
                now,
            ),
        )

        out.append({
            "source_type": "marketaux",
            "source_label": a.get("source"),
            "headline": a.get("title"),
            "summary": a.get("description") or a.get("snippet"),
            "link": a.get("url"),
            "timestamp": published_at,
            "relevance_score": a.get("relevance_score"),
            "entities": a.get("entities"),
        })

    conn.commit()
    conn.close()

    print(f"[MARKETAUX] Ingested {len(out)} MarketAux articles")
    return out
