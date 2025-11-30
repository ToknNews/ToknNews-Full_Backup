#!/usr/bin/env python3
# =========================================================
# TOKNNews Database Utility Layer  (SQLite)
# =========================================================
import sqlite3
import os
from contextlib import contextmanager

DB_PATH = "/var/www/toknnews/data/toknnews.db"

# Ensure DB exists
if not os.path.exists(DB_PATH):
    raise FileNotFoundError(f"Database not found: {DB_PATH}")

@contextmanager
def get_conn():
    """Context-managed connection with row factory and safe close."""
    conn = sqlite3.connect(DB_PATH, timeout=30, isolation_level=None)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Re-initialize schema if needed."""
    schema_file = "/var/www/toknnews/schema.sql"
    if not os.path.exists(schema_file):
        raise FileNotFoundError("schema.sql missing.")
    with open(schema_file) as f:
        schema = f.read()
    with get_conn() as conn:
        conn.executescript(schema)

def insert_scene(scene_id, headline, source, sentiment=None, url=None):
    """Insert a new scene record (compiler-safe)."""
    sql = """INSERT OR IGNORE INTO scenes
             (id, headline, source, sentiment, url)
             VALUES (?, ?, ?, ?, ?);"""
    with get_conn() as conn:
        conn.execute(sql, (scene_id, headline, source, sentiment, url))

def update_prompt(scene_id, summary, sora_prompt, score):
    """Update summary + Sora prompt once generated."""
    sql = """UPDATE scenes
             SET summary=?, sora_prompt=?, prompt_score=?, render_status='ready'
             WHERE id=?;"""
    with get_conn() as conn:
        conn.execute(sql, (summary, sora_prompt, score, scene_id))

def fetch_recent(limit=10):
    """Fetch most recent scenes."""
    sql = "SELECT * FROM scenes ORDER BY created_at DESC LIMIT ?;"
    with get_conn() as conn:
        cur = conn.execute(sql, (limit,))
        return [dict(row) for row in cur.fetchall()]
