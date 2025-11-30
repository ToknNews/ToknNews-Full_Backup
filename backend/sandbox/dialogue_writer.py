#!/usr/bin/env python3
"""
ToknNews Dialogue Writer (Sandbox)
----------------------------------
Takes a structured scene summary or headline and rewrites it
as natural spoken commentary in Chip's voice style.

Dry-run by default: prints output to console before writing.
"""

import os, sys, json
from datetime import datetime
from openai import OpenAI
from metrics_logger import log_metric
from textblob import TextBlob

# === CONFIG ===
GO_LIVE = False  # change to True to write to chip_latest.txt
INPUT_SCENE_PATH = "/var/www/toknnews/devdata/latest_scene.json"
OUTPUT_PATH = "/var/www/toknnews/devdata/audio_scripts/chip_latest.txt"

# === OpenAI client ===
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# === LOAD scene ===
if not os.path.exists(INPUT_SCENE_PATH):
    sys.exit(f"[Error] Missing {INPUT_SCENE_PATH}")

with open(INPUT_SCENE_PATH, "r") as f:
    scene = json.load(f)

headline = scene.get("topic", "")
summary = scene.get("script", "")
if not headline and not summary:
    sys.exit("[Error] No content found in scene file.")

# === PROMPT TEMPLATE ===
prompt = f"""
You are "Chip", the calm and confident AI news anchor for ToknNews.
Rewrite the following news item as a short spoken commentary (3-5 sentences).
Keep it conversational and realistic for voice delivery.
Avoid bullet points, keep sentences under 20 words, and vary rhythm.
If it’s exciting news, show subtle energy; if routine, keep tone steady.

Headline: {headline}
Summary: {summary}
"""

print("\n=== Dialogue Writer (Sandbox) ===")
print(f"Input: {INPUT_SCENE_PATH}")
print(f"GO_LIVE: {GO_LIVE}")
print("==============================\n")

# === GENERATE dialogue ===
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a professional AI news anchor."},
                  {"role": "user", "content": prompt}],
        temperature=0.8,
        max_tokens=250
    )
    chip_dialogue = response.choices[0].message.content.strip()

    # --- METRICS LOGGING ---
    log_metric("dialogue_chars", len(chip_dialogue))
    log_metric("dialogue_sentences", chip_dialogue.count("."))
    # --- SENTIMENT ANALYSIS ---
    sentiment_score = round(TextBlob(chip_dialogue).sentiment.polarity, 3)
    log_metric("dialogue_sentiment", sentiment_score, {"text_sample": chip_dialogue[:100]})

except Exception as e:
    sys.exit(f"[Error] OpenAI generation failed: {e}")

print("🗣️  Generated Chip Dialogue:\n")
print(chip_dialogue)
print("\n==============================\n")

if not GO_LIVE:
    print("[Dry Run] Preview only. No file written.\n")
    sys.exit(0)

# === WRITE output when live ===
os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
with open(OUTPUT_PATH, "w") as f:
    f.write(chip_dialogue)

print(f"[Saved] Dialogue written to {OUTPUT_PATH}")
