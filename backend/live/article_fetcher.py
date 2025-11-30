#!/usr/bin/env python3
"""
TOKNNews Article Fetcher (v3.5)
Hardened extractor with:
 - UA spoofing
 - AMP + mobile fallback
 - LD+JSON extraction (articleBody)
 - Coindesk JSON payload extraction
 - Anti-empty-document fallback
"""

import requests
from readability import Document
from bs4 import BeautifulSoup
import json, re

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/119.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "sec-ch-ua": '"Chromium";v="119", "Not=A?Brand";v="24", "Google Chrome";v="119"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"'
}


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


# ------------------------------------------------------
# LD+JSON extraction
# ------------------------------------------------------
def extract_ld_json(html):
    soup = BeautifulSoup(html, "html.parser")
    blocks = soup.find_all("script", type="application/ld+json")

    for block in blocks:
        try:
            data = json.loads(block.get_text(strip=True))
            if isinstance(data, dict):
                if "articleBody" in data:
                    return clean(data["articleBody"])
                if "description" in data:
                    return clean(data["description"])
        except:
            pass

    return ""


# ------------------------------------------------------
# Coindesk embedded JSON payload extractor
# ------------------------------------------------------
def extract_coindesk_payload(html):
    """
    Coindesk often embeds the full article text inside:
      window.__data = {...}
    """

    match = re.search(r"window\.__data\s*=\s*({.*});</script>", html, re.DOTALL)
    if not match:
        return ""

    try:
        data = json.loads(match.group(1))
        # Coindesk articleBody lives deep in this JSON
        for k in ("article", "page", "post", "content"):
            if k in data and isinstance(data[k], dict):
                body = data[k].get("body") or data[k].get("articleBody")
                if body:
                    return clean(body)
    except Exception:
        return ""

    return ""


# ------------------------------------------------------
# BeautifulSoup fallback
# ------------------------------------------------------
def bs_extract(html):
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "header", "footer", "nav"]):
        tag.extract()

    chunks = []
    for p in soup.find_all(["p", "div"]):
        txt = clean(p.get_text())
        if len(txt) > 60:
            chunks.append(txt)

    return clean(" ".join(chunks))


# ------------------------------------------------------
# Main fetch
# ------------------------------------------------------
def fetch_html(url):
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.text
    except:
        return ""
    return ""


def fetch_article(url):
    if not url:
        return ""

    # 1. Primary fetch
    html = fetch_html(url)
    if not html or len(html) < 50:
        return ""

    # 2. Coindesk JSON payload
    payload = extract_coindesk_payload(html)
    if len(payload) > 200:
        return payload

    # 3. LD+JSON extraction
    ldjson = extract_ld_json(html)
    if len(ldjson) > 200:
        return ldjson

    # 4. Readability
    try:
        doc = Document(html)
        cleaned = clean(re.sub(r"<[^>]+>", " ", doc.summary()))
        if len(cleaned) > 200:
            return cleaned
    except:
        pass

    # 5. BS fallback
    bs = bs_extract(html)
    if len(bs) > 200:
        return bs

    # 6. Try AMP
    amp = fetch_html(url.rstrip("/") + "/amp")
    if amp:
        ldjson = extract_ld_json(amp)
        if len(ldjson) > 200:
            return ldjson
        bs = bs_extract(amp)
        if len(bs) > 200:
            return bs

    # 7. Try mobile version
    mobile = fetch_html(url.replace("https://www.", "https://m."))
    if mobile:
        ldjson = extract_ld_json(mobile)
        if len(ldjson) > 200:
            return ldjson
        bs = bs_extract(mobile)
        if len(bs) > 200:
            return bs

    return ""
