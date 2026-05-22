import sqlite3

def connect_sqlite(path: str):
    conn = sqlite3.connect(
        path,
        timeout=60,
        check_same_thread=False
    )
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA synchronous=NORMAL;")
    conn.execute("PRAGMA busy_timeout = 30000;")
    return conn
