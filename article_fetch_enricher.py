#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝

TOKNNEWS ENRICHMENT ENGINE
Article Fetch Enricher

Purpose
-------
Fetches article content from raw URLs and extracts concise context
for downstream story processing.

Primary Input
-------------
/opt/toknnews/data/show_structure.json

Primary Output
--------------
/opt/toknnews/data/article_enrichment.json

Design Rules
------------
• Safe (never crash on bad URLs)
• Deterministic structure
• Minimal summaries
• No prompt injection
• No massive text output
• No OpenClaw dependency

Author: TOKN Systems
"""

from __future__ import annotations

import json
import time
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

INPUT_PATH = Path("/opt/toknnews/data/show_structure.json")
OUTPUT_PATH = Path("/opt/toknnews/data/article_enrichment.json")
TMP_OUTPUT_PATH = OUTPUT_PATH.with_suffix(".tmp")

# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

REQUEST_TIMEOUT = 6
MAX_ARTICLES = 15
MAX_TEXT_CHARS = 2000

HEADERS = {
    "User-Agent": "Mozilla/5.0 (ToknNewsBot)"
}

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def now_ts() -> float:
    return time.time()

def atomic_write(path: Path, tmp: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    tmp.replace(path)

# ---------------------------------------------------------
# FETCH
# ---------------------------------------------------------

def fetch_url_text(url: str) -> str:
    try:
        resp = requests.get(url, timeout=REQUEST_TIMEOUT, headers=HEADERS)
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.text, "html.parser")

        # Extract visible text blocks
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)

        return text[:MAX_TEXT_CHARS]

    except Exception:
        return ""

# ---------------------------------------------------------
# LIGHT SUMMARY
# ---------------------------------------------------------

def extract_summary(text: str) -> Dict[str, str]:
    if not text:
        return {
            "summary": "",
            "key_takeaway": "",
            "confidence": 0.0
        }

    sentences = text.split(". ")

    summary = sentences[0][:200] if sentences else ""
    key = sentences[1][:200] if len(sentences) > 1 else summary

    return {
        "summary": summary.strip(),
        "key_takeaway": key.strip(),
        "confidence": 0.7 if summary else 0.0
    }

# ---------------------------------------------------------
# MAIN BUILDER
# ---------------------------------------------------------

def build_enrichment(show_structure: Dict[str, Any]) -> List[Dict[str, Any]]:
    results = []
    seen = set()

    for act in show_structure.get("acts", []):
        for story in act.get("stories", []):
            url = clean(story.get("raw_url"))
            entity = clean(story.get("entity"))

            if not url or url in seen:
                continue

            seen.add(url)

            text = fetch_url_text(url)
            summary_data = extract_summary(text)

            results.append({
                "url": url,
                "entity": entity,
                "domain": clean(act.get("domain")),
                "summary": summary_data["summary"],
                "key_takeaway": summary_data["key_takeaway"],
                "confidence": summary_data["confidence"]
            })

            if len(results) >= MAX_ARTICLES:
                return results

    return results

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError("Missing show_structure.json")

    show_structure = json.loads(INPUT_PATH.read_text())

    enrichment = build_enrichment(show_structure)

    payload = {
        "generated_at": now_ts(),
        "count": len(enrichment),
        "articles": enrichment
    }

    atomic_write(OUTPUT_PATH, TMP_OUTPUT_PATH, payload)

    print(f"[ENRICHMENT] articles={len(enrichment)}")

if __name__ == "__main__":
    main()
