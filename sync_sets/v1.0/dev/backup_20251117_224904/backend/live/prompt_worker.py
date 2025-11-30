#!/usr/bin/env python3
# =========================================================
# TOKNNews Prompt Worker  v1.0
# =========================================================
# Watches SQLite ledger for new scenes without sora_prompt,
# enriches them with summaries and Sora2-ready prompts,
# and appends each result to /data/prompts/feed.jsonl.
#
# Runs safely under PM2 as:  toknnews-prompts
# =========================================================

import os, json, time, uuid, random, hashlib
import sqlite3, requests
from newspaper import Article
import random
from contextlib import closing
from datetime import datetime
from db import update_prompt, get_conn

DB_PATH = "/var/www/toknnews/data/toknnews.db"
PROMPT_FEED = "/var/www/toknnews/data/prompts/feed.jsonl"
CHECK_INTERVAL = 60  # seconds between DB scans
BATCH_SIZE = 10      # process 10 new scenes at a time

# ---------------------------------------------------------
#  CHIP Hybrid Action-Dialogue Sora2 Prompt Builder
# ---------------------------------------------------------
import random
from newspaper import Article

def extract_article_text(url):
    """Pull 1-2 paragraphs from an article for factual dialogue."""
    if not url:
        return ""
    try:
        art = Article(url)
        art.download()
        art.parse()
        text = art.text.strip().split("\n")
        paras = [p for p in text if p.strip()][:2]
        return " ".join(paras)
    except Exception:
        return ""

def build_sora_prompt(headline, summary, sentiment, url=None):
    """
    Generates cinematic newsroom prose with interleaved dialogue.
    Each scene contains motion, Chip's voice, and a natural transition.
    """

    # --- get body context ---
    article_text = extract_article_text(url)
    context = (article_text or summary or "").replace("\n", " ").strip()
    facts = " ".join(context.split(".")[:2]).strip() + "."

    # --- base motion vocab ---
    camera_moves = [
        "camera pans slowly across the ToknNews studio",
        "steady dolly-in toward Chip at the holographic desk",
        "camera drifts gently through the cool LED light"
    ]
    chip_actions = [
        "adjusts his notes", "leans toward the prompter",
        "taps the glass desk", "straightens his cuff"
    ]
    background_moves = [
        "tickers ripple behind him", "LED panels shift hue",
        "data streams crawl across the rear screen"
    ]
    closers = [
        "He nods once as lights rebalance for the next headline.",
        "He glances to the side monitor, cueing the following story.",
        "He steadies his papers, ready for the next segment."
    ]

    # --- sentiment-driven phrasing ---
    if sentiment == "bullish":
        mood = ("grins", "with upbeat confidence")
        hijinx = "He chuckles. “The bulls finally found their morning coffee.”"
        transition = "“In other news, optimism isn’t the only thing on the rise.”"
    elif sentiment == "bearish":
        mood = ("speaks", "in a dry, even tone")
        hijinx = "He smirks. “Gravity’s undefeated.”"
        transition = "“In other news, a few bright spots refuse to follow the trend.”"
    else:
        mood = ("explains", "with calm professionalism")
        hijinx = ""
        transition = "“In other news, here’s what else moved the markets today.”"

    # --- build paragraph ---
    line1 = (
        f"The {random.choice(camera_moves)} as Chip {random.choice(chip_actions)}. "
        f"“{headline.strip()},” he {mood[0]} {mood[1]}."
    )
    line2 = (
        f"While {random.choice(background_moves)}, he continues: "
        f"“{facts.strip()}”"
    )
    line3 = " ".join(filter(None, [hijinx, transition, random.choice(closers)]))

    return f"{line1} {line2} {line3}"

# ---------------------------------------------------------
#  Helper: fetch short article summary from URL (if any)
# ---------------------------------------------------------
def fetch_summary(url):
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=5, headers={"User-Agent": "Mozilla/5.0"})
        text = resp.text
        # basic first-paragraph extraction
        start = text.find("<p>")
        end = text.find("</p>", start)
        if start != -1 and end != -1:
            snippet = text[start+3:end]
            return snippet.strip()[:400]
        return ""
    except Exception:
        return ""

# ---------------------------------------------------------
#  Helper: select scenes missing prompts
# ---------------------------------------------------------
def get_pending_scenes(limit=BATCH_SIZE):
    with get_conn() as conn:
        cur = conn.execute("""
            SELECT id, headline, source, sentiment, url
            FROM scenes
            WHERE sora_prompt IS NULL
            ORDER BY created_at DESC
            LIMIT ?;
        """, (limit,))
        return [dict(row) for row in cur.fetchall()]

# ---------------------------------------------------------
#  Article Extraction Helper
# ---------------------------------------------------------
def extract_article_text(url):
    """Pull 1–2 short paragraphs of article body for richer prompts."""
    if not url:
        return ""
    try:
        art = Article(url)
        art.download()
        art.parse()
        text = art.text.strip().split("\n")
        paras = [p for p in text if p.strip()][:2]
        return " ".join(paras)
    except Exception:
        return ""

# ---------------------------------------------------------
#  Append prompt to feed file
# ---------------------------------------------------------
def append_to_feed(scene_id, headline, prompt):
    os.makedirs(os.path.dirname(PROMPT_FEED), exist_ok=True)
    entry = {"scene_id": scene_id, "headline": headline, "sora_prompt": prompt, "generated_at": datetime.utcnow().isoformat()}
    tmp = PROMPT_FEED + ".tmp"
    with open(tmp, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    os.replace(tmp, PROMPT_FEED)

# ---------------------------------------------------------
#  Worker main loop
# ---------------------------------------------------------
def main():
    print("[PromptWorker] started. Watching for new scenes.")
    while True:
        scenes = get_pending_scenes()
        if not scenes:
            time.sleep(CHECK_INTERVAL)
            continue

        for s in scenes:
            headline = s["headline"]
            sentiment = s.get("sentiment", "neutral")
            url = s.get("url")

            summary = fetch_summary(url)
            sora_prompt = build_sora_prompt(headline, summary, sentiment)
            prompt_score = round(random.uniform(0.6, 0.98), 2)

            update_prompt(s["id"], summary, sora_prompt, prompt_score)
            append_to_feed(s["id"], headline, sora_prompt)

            print(f"[PromptWorker] + {headline[:60]}...")

        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
