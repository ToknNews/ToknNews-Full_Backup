#!/usr/bin/env python3
"""
rss_grok_enricher.py
ToknNews — Production Grok Enrichment (RSS + API)

Responsibilities:
- Selectively enrich raw content items via Grok (xAI)
- Persist structured analysis to SQLite
- Never block ingestion
- Never re-enrich the same item
"""

import os
import time
import json
import logging

from backend.runtime.grok_client import call_grok
from backend.runtime.sqlite_utils import connect_sqlite

# --------------------------------------------------
# LOGGING
# --------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("grok_enricher")

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
DB_PATH = "/opt/toknnews/data/ingestion/ingestion.db"

ENABLE_GROK_ENRICH = os.getenv("ENABLE_GROK_ENRICH", "false").lower() == "true"
MAX_ENRICH_PER_RUN = int(os.getenv("MAX_ENRICH_PER_RUN", "20"))

# --------------------------------------------------
# SOURCE-SPECIFIC ENRICHMENT CONTROLS
# --------------------------------------------------

# Max enrichments per source_label per run
SOURCE_ENRICH_CAPS = {
    "federalreserve": 2,   # keep Fed, but cap hard
    "rss": 2,              # fallback / unknown rss
}

# Suppress low-signal regulatory boilerplate
FED_EXCLUDE_KEYWORDS = [
    "announces approval",
    "announces reappointment",
    "announces termination",
    "requests public input",
    "publishes its",
    "publishes first of",
    "issues guidance",
    "threshold",
    "manual",
    "exemption",
    "application by",
]

ALLOWED_SOURCES = {
    # Core US financial
    "coindesk.com",
    "reuters.com",
    "bloomberg.com",
    "finance.yahoo.com",
    "wsj.com",
    "cnbc.com",
    "marketwatch.com",
    "benzinga.com",

    # Crypto-native
    "cryptoslate.com",
    "bitcoinmagazine.com",
    "decrypt.co",
    "cointelegraph.com",
}

# --------------------------------------------------
# NORMALIZATION HELPERS
# --------------------------------------------------

def is_ascii_english(text: str) -> bool:
    """
    Deterministic language filter.
    Rejects non-ASCII headlines (JP, CN, Cyrillic, etc).
    """
    if not text:
        return False
    try:
        text.encode("ascii")
        return True
    except UnicodeEncodeError:
        return False


def normalize_source_label(label: str) -> str:
    """
    Normalize source labels across RSS and MarketAux.
    """
    if not label:
        return ""

    label = label.lower().strip()

    SOURCE_MAP = {
        "bloomberg": "bloomberg.com",
        "cryptoslate": "cryptoslate.com",
        "bitcoinmagazine": "bitcoinmagazine.com",
        "decrypt": "decrypt.co",
        "cointelegraph": "cointelegraph.com",
        "finance.yahoo.com": "finance.yahoo.com",
        "benzinga.com": "benzinga.com",
        "investing.com": "investing.com",
        "wsj": "wsj.com",
        "cnbc": "cnbc.com",
        "marketwatch": "marketwatch.com",
    }

    return SOURCE_MAP.get(label, label)

# --------------------------------------------------
# JSON EXTRACTION
# --------------------------------------------------

def extract_json_from_grok_response(text: str) -> dict | None:
    """
    Extract the first valid JSON object from a Grok response.
    Handles tool blocks and markdown fences.
    """
    if not text:
        return None

    text = text.strip()

    # Fast path: already pure JSON
    if text.startswith("{") and text.endswith("}"):
        try:
            return json.loads(text)
        except Exception:
            return None

    # Look for fenced JSON block
    if "```json" in text:
        try:
            json_part = text.split("```json", 1)[1].split("```", 1)[0]
            return json.loads(json_part.strip())
        except Exception:
            return None

    # Fallback: try to find first { ... } block
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None

    return None

# --------------------------------------------------
# PROMPT
# --------------------------------------------------

def build_grok_prompt(url: str, headline: str, summary: str = "") -> str:
    return f"""
Read this full article and enrich for ToknNews autonomous broadcast:

URL: {url}
Headline: {headline}
Summary snippet: {summary[:300]}

Extract and analyze:
- 3-5 key concrete facts (numbers, names, dates, events)
- Core implication for crypto markets or risk assets
- Any on-chain, regulatory, or macro angle
- Broader sentiment or culture vibe (bullish/bearish/chaotic)
- One standout quote if relevant

Use browse_page to read the full content. Supplement with web_search or x_semantic_search if needed.

Return JSON only:
{{
  "facts": ["fact1", "fact2"],
  "implication": "1-2 sentence analysis",
  "angles": {{"onchain": "", "regulatory": "", "macro": ""}},
  "sentiment": "bullish | bearish | neutral | chaotic",
  "quote": "",
  "grok_take": "Your unfiltered insight in 1 sentence",
  "anchor_take": "How a ToknNews anchor would say this in one line"
}}
"""

# --------------------------------------------------
# CORE ENRICHER
# --------------------------------------------------

def enrich_recent_rss():
    if not ENABLE_GROK_ENRICH:
        log.info("[GROK] Enrichment disabled by env flag.")
        return

    conn = connect_sqlite(DB_PATH)
    cur = conn.cursor()

    source_counts = {}

    # Pull a wider candidate window to allow source diversification
    cur.execute(
        """
        SELECT id, headline, link, summary, source_type, source_label
        FROM raw_content_items
        WHERE link IS NOT NULL
        AND id NOT IN (
            SELECT raw_item_id
            FROM rss_grok_enrichment
            WHERE raw_item_id IS NOT NULL
        )
        ORDER BY id DESC
        LIMIT ?
        """,
        (MAX_ENRICH_PER_RUN * 5,),
    )

    raw_rows = cur.fetchall()

    sanitized_rows = []
    for row in raw_rows:
        raw_id, headline, link, summary, source_type, source_label = row

        # 1️⃣ Reject non-English / non-ASCII headlines
        if not is_ascii_english(headline):
            continue

        # 2️⃣ Enforce source allowlist (RSS + MarketAux)
        normalized = normalize_source_label(source_label)
        if normalized not in ALLOWED_SOURCES:
            continue

        sanitized_rows.append(row)

    log.info(
        f"[GROK] Candidates → {len(sanitized_rows)} "
        f"(sanitized from {len(raw_rows)})"
    )

    for raw_id, headline, link, summary, source_type, source_label in sanitized_rows:
        try:
            label = (source_label or "").lower()
            headline_l = (headline or "").lower()

            # Enforce per-source caps
            count = source_counts.get(label, 0)
            cap = SOURCE_ENRICH_CAPS.get(label)
            if cap is not None and count >= cap:
                continue

            # Filter Fed boilerplate
            if label == "federalreserve":
                if any(k in headline_l for k in FED_EXCLUDE_KEYWORDS):
                    continue

            prompt = build_grok_prompt(
                url=link,
                headline=headline,
                summary=summary or ""
            )

            response = call_grok(prompt=prompt, max_tokens=400)
            data = extract_json_from_grok_response(response)

            if not data:
                log.error(
                    "[GROK] Could not extract JSON, skipping. "
                    f"Headline='{headline[:60]}', "
                    f"Response preview='{(response or '')[:120]}'"
                )
                continue

            cur.execute(
                """
                INSERT OR IGNORE INTO rss_grok_enrichment
                (raw_item_id, url, headline, enrichment_json, sentiment, grok_take, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    raw_id,
                    link,
                    headline,
                    json.dumps(data),
                    data.get("sentiment"),
                    data.get("grok_take"),
                    int(time.time()),
                ),
            )

            # Increment count only after successful insert
            source_counts[label] = source_counts.get(label, 0) + 1

            log.info(
                f"[GROK] Enriched ({source_type}:{source_label}) → {headline[:80]}"
            )

        except Exception as e:
            log.error("[GROK] Enrichment failed:", exc_info=e)
            continue

    conn.commit()
    conn.close()
