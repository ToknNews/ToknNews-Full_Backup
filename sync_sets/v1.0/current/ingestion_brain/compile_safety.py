#!/usr/bin/env python3
"""
TOKNNews Compile Safety Layer
Handles atomic writes, validation, compile logging,
and continuity tracking.
"""

import os, json, time, tempfile, shutil

DATA_DIR = "/var/www/toknnews/data"
LOG_FILE = os.path.join(DATA_DIR, "compile_log.jsonl")
CONTINUITY_FILE = os.path.join(DATA_DIR, "continuity_log.json")

# ------------------------------------------------------------
# Atomic JSON writer
# ------------------------------------------------------------
def atomic_write(path: str, data: dict | list):
    """Write JSON atomically to avoid corruption."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = tempfile.NamedTemporaryFile("w", delete=False, dir=os.path.dirname(path))
    json.dump(data, tmp, indent=2)
    tmp.flush()
    os.fsync(tmp.fileno())
    tmp.close()
    shutil.move(tmp.name, path)

# ------------------------------------------------------------
# Compile logger
# ------------------------------------------------------------
def log_compile(headline: str, sentiment: str, next_topic: str, runtime: float, ok: bool = True, err: str = None):
    """Append compile metadata to JSONL log."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "headline": headline,
        "sentiment": sentiment,
        "next_topic": next_topic,
        "runtime": runtime,
        "status": "success" if ok else "error",
        "error": err or ""
    }
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry

# ------------------------------------------------------------
# Continuity tracker
# ------------------------------------------------------------
def update_continuity(last_topic: str, new_topic: str, next_topic: str, sentiment: str, segue: str):
    """Maintain a rolling continuity log of segues and tone."""
    os.makedirs(os.path.dirname(CONTINUITY_FILE), exist_ok=True)
    try:
        log = json.load(open(CONTINUITY_FILE)) if os.path.exists(CONTINUITY_FILE) else []
    except Exception:
        log = []
    entry = {
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "from": last_topic,
        "to": new_topic,
        "next": next_topic,
        "sentiment": sentiment,
        "segue": segue
    }
    log.append(entry)
    log = log[-10:]  # keep last 10 transitions
    atomic_write(CONTINUITY_FILE, log)
    return entry

# ------------------------------------------------------------
# Output validator
# ------------------------------------------------------------
def validate_scene(scene_blocks: list):
    """Basic integrity check before final export."""
    if not isinstance(scene_blocks, list) or len(scene_blocks) < 3:
        raise ValueError("Invalid scene block structure.")
    for block in scene_blocks:
        if "block" not in block or "text" not in block:
            raise ValueError(f"Malformed block: {block}")
        if not block["text"].strip():
            raise ValueError(f"Empty text in block: {block['block']}")
    return True
