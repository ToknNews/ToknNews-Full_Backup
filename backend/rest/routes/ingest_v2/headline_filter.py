#!/usr/bin/env python3
import re

# 2025 — ONLY REAL BREAKING NEWS SURVIVES
BORING_PATTERNS = [
    r"(?i)how.*blockchain",
    r"(?i)what is",
    r"(?i)explaining",
    r"(?i)beginner.?s?.*guide",
    r"(?i)introduction to",
    r"(?i)ultimate guide",
    r"(?i)vs\.?",
    r"(?i)which is better",
    r"(?i)comparing",
    r"(?i)understanding",
    r"(?i)from idea to",
    r"(?i)a look at",
    r"(?i)the basics of",
    r"(?i)101$",
    r"(?i)^top \d+",
    r"(?i)best \d+",
    r"(?i)\d+.*(tips|tricks|ways)",
    r"(?i)why you should",
    r"(?i)the future of",
    r"(?i)is dead",
    r"(?i)is the new"
]

def is_real_news(headline):
    if len(headline) < 40:
        return False  # too short = clickbait
    if any(re.search(pattern, headline) for pattern in BORING_PATTERNS):
        return False
    # Must contain at least one of these high-signal words
    signal_words = ["raises", "launches", "files", "acquires", "hacked", "exploit", "delay", "ban", "approved", "rejected", "surge", "crash", "rug", "whale", "dump", "pump", "etf", "sec", "lawsuit", "partnership"]
    if not any(word in headline.lower() for word in signal_words):
        return False
    return True

# Apply in enrich.py or run_cycle.py
def filter_stories(stories):
    return [s for s in stories if is_real_news(s["headline"])]
