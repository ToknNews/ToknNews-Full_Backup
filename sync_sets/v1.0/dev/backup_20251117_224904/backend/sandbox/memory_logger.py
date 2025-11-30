#!/usr/bin/env python3
# Purpose: Insert the latest spoken lines into a sandbox SQLite DB (memories.db)
# Scope:   Dev-only (reads chip_latest.txt + latest_narrative.json)
# Output:  /var/www/toknnews/devdata/memories.db → table: memories

import os, sqlite3, json
from datetime import datetime, timezone

# === MiniLM local embedding model (offline) ===
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")

DEV_ROOT = "/var/www/toknnews/devdata"
AUDIO_DIR = os.path.join(DEV_ROOT, "audio_scripts")
TXT_PATH  = os.path.join(AUDIO_DIR, "chip_latest.txt")
NARR_PATH = "/var/www/toknnews/data/latest_narrative.json"  # contains topic
DB_PATH   = os.path.join(DEV_ROOT, "memories.db")

def ensure_schema(conn):
    conn.execute("""
    CREATE TABLE IF NOT EXISTS memories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        character TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        topic TEXT,
        text TEXT NOT NULL,
        sentiment TEXT,
        source TEXT,
        embedding BLOB
    );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_char_time ON memories(character, timestamp);")

def load_dialogue_lines():
    if not os.path.exists(TXT_PATH):
        return []
    with open(TXT_PATH, "r", encoding="utf-8") as f:
        lines = [ln.strip() for ln in f.readlines()]
    return [ln for ln in lines if ln]  # drop blanks

def load_topic():
    try:
        if os.path.exists(NARR_PATH):
            with open(NARR_PATH, "r", encoding="utf-8") as f:
                return (json.load(f).get("topic") or "").strip()
    except Exception:
        pass
    return ""

def main():
    lines = load_dialogue_lines()
    if not lines:
        print("[Mem] No dialogue lines found; nothing to insert.")
        return

    topic = load_topic()
    ts = datetime.now(timezone.utc).isoformat()
    character = "Chip"
    source = "ToknNews-Dev"
    sentiment = None  # optional: fill later from compiler if available

    os.makedirs(DEV_ROOT, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        ensure_schema(conn)

        # === Generate embeddings for each dialogue line ===
        records = []
        for line in lines:
            try:
                emb = model.encode(line).tolist()       # 384-dim MiniLM vector
                emb_json = json.dumps(emb)
            except Exception as e:
                print(f"[Mem] ⚠️ Embedding failed for line: {e}")
                emb_json = None

            records.append((character, ts, topic, line, sentiment, source, emb_json))

        conn.executemany(
            """INSERT INTO memories (character, timestamp, topic, text, sentiment, source, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            records
        )
        conn.commit()
        print(f"[Mem] 🧠 Inserted {len(lines)} lines with embeddings → {DB_PATH}")

    finally:
        conn.close()

if __name__ == "__main__":
    main()
