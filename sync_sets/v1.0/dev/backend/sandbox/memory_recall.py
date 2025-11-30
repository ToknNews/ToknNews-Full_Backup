#!/usr/bin/env python3
"""
memory_recall.py — semantic recall for ToknNews Memory DB
Compares a new query sentence to all stored memories using cosine similarity.
"""

import sqlite3, json, numpy as np, sys, os
from sentence_transformers import SentenceTransformer

DB_PATH = "/var/www/toknnews/devdata/memories.db"
model = SentenceTransformer("all-MiniLM-L6-v2")

def recall(query_text, top_k=5):
    if not os.path.exists(DB_PATH):
        print(f"[Recall] ❌ No memory DB found at {DB_PATH}")
        return

    # Get query embedding
    query_vec = np.array(model.encode(query_text), dtype=np.float32)

    # Fetch memories
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT id, character, topic, text, embedding FROM memories WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        print("[Recall] No memories with embeddings found.")
        return

    # Compute cosine similarity
    sims = []
    for rid, character, topic, text, emb_json in rows:
        try:
            emb = np.array(json.loads(emb_json), dtype=np.float32)
            sim = np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb))
            sims.append((sim, rid, character, topic, text))
        except Exception:
            continue

    # Sort by similarity
    sims.sort(reverse=True, key=lambda x: x[0])
    top = sims[:top_k]

    print(f"\n[Recall] 🔎 Top {top_k} most similar memories to:\n“{query_text}”\n")
    for score, rid, character, topic, text in top:
        print(f"→ {score:.3f} | {character} | {topic}\n   {text}\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 memory_recall.py 'your query text'")
    else:
        recall(" ".join(sys.argv[1:]))
