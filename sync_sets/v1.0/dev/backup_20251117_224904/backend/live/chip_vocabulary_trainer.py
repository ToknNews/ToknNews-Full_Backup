#!/usr/bin/env python3
# =========================================================
# ToknNews Chip Vocabulary Trainer v1.1
# =========================================================
import os, re, json, glob
from pathlib import Path

FEED_GLOBS = [
    "/var/www/toknnews/data/raw/*.json",
    "/var/www/toknnews/data/feeds/*.json"
]
VOCAB_PATH = "/var/www/toknnews/data/chip_vocabulary.json"

def collect_text():
    texts = []
    for g in FEED_GLOBS:
        for f in glob.glob(g):
            try:
                data = json.load(open(f))
                items = data.get("items") if isinstance(data, dict) else data
                if not items:
                    continue
                for item in items:
                    t = " ".join([
                        item.get("headline",""),
                        item.get("title",""),
                        item.get("summary",""),
                        item.get("description","")
                    ])
                    if t.strip():
                        texts.append(t)
            except Exception:
                continue
    return texts

def extract_vocab(texts):
    verbs, sentiments, transitions = set(), set(), set()
    verb_pat = r"\b(rallies|spikes|edges higher|rebounds|slides|tumbles|surges|plunges|extends gains)\b"
    sent_pat = r"\b(optimism|caution|momentum|volatility|headwinds|pressure|recovery)\b"
    trans_pat = r"\b(in other news|meanwhile|elsewhere|on the flip side|looking ahead)\b"
    for t in texts:
        verbs.update(re.findall(verb_pat, t, flags=re.I))
        sentiments.update(re.findall(sent_pat, t, flags=re.I))
        transitions.update(re.findall(trans_pat, t, flags=re.I))
    return {
        "market_verbs": sorted(verbs),
        "sentiment_phrases": sorted(sentiments),
        "transitions": sorted(transitions)
    }

def main():
    texts = collect_text()
    if not texts:
        print("⚠️ No feed text found.")
        return
    vocab = extract_vocab(texts)
    Path(os.path.dirname(VOCAB_PATH)).mkdir(parents=True, exist_ok=True)
    json.dump(vocab, open(VOCAB_PATH,"w"), indent=2)
    print(f"✅ Chip vocabulary updated → {VOCAB_PATH}")

if __name__ == "__main__":
    main()
