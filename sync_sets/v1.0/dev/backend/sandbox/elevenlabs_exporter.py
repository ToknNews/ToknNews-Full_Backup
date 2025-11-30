#!/usr/bin/env python3
"""
ElevenLabs Exporter (Dev Sandbox)
Extracts dialogue lines from latest_narrative.json and saves SSML.
Output: /var/www/toknnews/devdata/audio_scripts/chip_latest.ssml
"""

import os, json, re, html

DATA_PATH = "/var/www/toknnews/data/latest_narrative.json"
OUT_DIR   = "/var/www/toknnews/devdata/audio_scripts"
OUT_FILE  = os.path.join(OUT_DIR, "chip_latest.ssml")

os.makedirs(OUT_DIR, exist_ok=True)

def extract_dialogue(narrative_text: str):
    """Pull everything between Unicode smart quotes “ ... ” or plain quotes."""
    # Decode any HTML entities and normalize quotes
    s = html.unescape(narrative_text)
    s = s.replace('\\"', '"').replace('”', '"').replace('“', '"')
    # Extract text between quotes
    lines = re.findall(r'"([^"]+)"', s)
    return [line.strip() for line in lines if line.strip()]

def make_ssml(dialogue_lines):
    """Wrap cleaned dialogue lines into SSML for ElevenLabs."""
    body = ""
    for line in dialogue_lines:
        body += f"    <p>{line}</p>\n    <break time='400ms'/>\n"
    return (
        "<speak>\n"
        "  <voice name='Chip'>\n"
        f"{body}"
        "  </voice>\n"
        "</speak>\n"
    )

def main():
    if not os.path.exists(DATA_PATH):
        print(f"[Exporter] ❌ Missing {DATA_PATH}")
        return
    data = json.load(open(DATA_PATH))
    narrative = data.get("narrative", "")
    dialogue_lines = extract_dialogue(narrative)
    if not dialogue_lines:
        print("[Exporter] ⚠️ No quoted dialogue found.")
        return
    ssml = make_ssml(dialogue_lines)
    with open(OUT_FILE, "w") as f:
        f.write(ssml)
    print(f"[Exporter] ✅ Wrote {len(dialogue_lines)} dialogue lines → {OUT_FILE}")
    # --- Also write a plain text copy for captions / Unreal ---
    txt_path = os.path.join(OUT_DIR, "chip_latest.txt")
    with open(txt_path, "w") as txt:
        for line in dialogue_lines:
            txt.write(line + "\n")
    print(f"[Exporter] 📝 Wrote plain text version → {txt_path}")

if __name__ == "__main__":
    main()
