#!/usr/bin/env python3
import sqlite3, sys, os

DB_PATH = "/var/www/toknnews/devdata/memories.db"

def show_latest(n=10):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""SELECT timestamp, character, topic, text
                   FROM memories ORDER BY id DESC LIMIT ?""", (n,))
    rows = cur.fetchall()
    conn.close()
    for r in rows:
        print(f"[{r[0]}] {r[1]} | {r[2]}\n  → {r[3]}\n")

def search(q):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""SELECT timestamp, character, topic, text
                   FROM memories WHERE text LIKE ? ORDER BY id DESC LIMIT 25""", (f"%{q}%",))
    rows = cur.fetchall()
    conn.close()
    for r in rows:
        print(f"[{r[0]}] {r[1]} | {r[2]}\n  → {r[3]}\n")

if __name__ == "__main__":
    if len(sys.argv) == 1:
        show_latest(10)
    elif sys.argv[1] == "latest":
        n = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        show_latest(n)
    elif sys.argv[1] == "search" and len(sys.argv) > 2:
        search(sys.argv[2])
    else:
        print("Usage: memory_query.py [latest N] | [search QUERY]")
