#!/usr/bin/env python3
import sys, os
sys.path.append("/var/www/toknnews-repo")
"""
TOKNNews — Unified Scene Compiler (Final V3 Integration)
Module C-5: Full structured-script integration

This compiler:
 - Accepts headline objects from ingestion
 - Calls Script Engine V3 for narrative timeline
 - Stores complete structured script in SQLite + snapshots
 - Preserves all dedupe logic, heartbeat logic, 
   daily_counts.json, scenes_snapshot.json, latest_scene.json

This file is a full replacement.
"""

import os, json, hashlib, sqlite3, textwrap, re
from datetime import datetime, timedelta, timezone
from collections import Counter

# === IMPORT: Script Engine V3 ===
from backend.script_engine.script_engine_v3 import generate_script


# === PATHS ===
DATA_DIR = "/var/www/toknnews/data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
MASTER_PATH = os.path.join(DATA_DIR, "scenes.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest_scene.json")
DB_PATH = os.path.join(DATA_DIR, "toknnews.db")
MAX_SCENES = 10000

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)


# === UTIL: strip HTML ===
def strip_html(s):
    if not s: return ""
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'https?://\S+', '', s)
    s = re.sub(r'\b\S+\.(jpg|jpeg|png|gif|webp|svg)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:1000]


# === UTIL: load RSS (used in Auto mode) ===
def load_rss_headlines(path="/var/www/toknnews/data/raw/rss_latest.json", limit=500):
    if not os.path.exists(path): return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        elif not isinstance(data, list):
            print("[RSS Loader] ⚠️ Unexpected data structure"); 
            return []
    except Exception as e:
        print(f"[RSS] Error loading {path}: {e}"); 
        return []

    scenes = []
    for item in data[:limit]:
        try:
            title = (item.get("title") or item.get("headline") or "").strip()
            if not title: continue
            summary = (item.get("summary","") + " " + item.get("description","")).strip()
            scenes.append({
                "time": item.get("timestamp") or datetime.utcnow().isoformat(),
                "character": "Chip",
                "topic": title,
                "source": item.get("source", "RSS"),
                "script": strip_html(summary),
                "status": "pending",
                "reply_to": None,
                "characters": "Chip",
            })
        except Exception as e:
            print(f"[RSS Loader] ⚠️ Skipped bad item: {e}"); 
            continue
    return scenes


# === DB Helper ===
def open_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS scenes(
            id TEXT PRIMARY KEY,
            time TEXT, character TEXT, topic TEXT, source TEXT,
            script TEXT, status TEXT, reply_to TEXT, characters TEXT, hash TEXT
        )
    """)
    return conn


# =====================================================================
# === MAIN COMPILER (STRUCTURED SCRIPT ENGINE ENABLED) ================
# =====================================================================

def compile_scene(headline, source="manual", character="chip"):
    """
    Main ToknNews scene compiler:
      - dedupe
      - call Script Engine V3
      - store structured timeline + metadata
      - refresh dashboard files
    """

    try:
        now_et = datetime.now(timezone(timedelta(hours=-5)))
        timestamp_iso = now_et.isoformat()

        # === DETERMINE TITLE ===
        if isinstance(headline, dict):
            title = headline.get("topic") or headline.get("title") or headline.get("headline") or ""
        else:
            title = str(headline)

        # === HASH FOR DEDUPE ===
        scene_hash = hashlib.md5(f"{source}:{title}".encode()).hexdigest()

        # === LOAD EXISTING ===
        existing = []
        if os.path.exists(MASTER_PATH):
            try:
                existing = json.load(open(MASTER_PATH)).get("scenes", [])
            except Exception:
                existing = []

        # === DEDUPE LAST 24 HOURS ===
        def to_naive_utc(ts_str):
            try:
                dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if dt.tzinfo:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt
            except Exception:
                return None

        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_hashes = set()
        for s in existing:
            t = s.get("time")
            if not t: continue
            dt = to_naive_utc(t)
            if dt and dt >= cutoff:
                h = s.get("hash")
                if h: recent_hashes.add(h)

        if scene_hash in recent_hashes:
            print("[SKIP] duplicate headline already exists in last-24-hour window")
            return

        # =====================================================================
        # === CALL SCRIPT ENGINE V3 (Core Upgrade in Module C-5) ===============
        # =====================================================================

        script_payload = generate_script(
            headline=title,
            article_context=headline.get("description","") if isinstance(headline, dict) else "",
            cluster_articles=None,
            character=character
        )

        # === AUDIO BLOCK RENDER (FINAL ROUTE VIA audio_block_renderer) ===
        from backend.script_engine.audio.audio_block_renderer import render_audio_blocks

        scene_id = script_payload["unreal"]["scene_id"]

        final_audio = render_audio_blocks(scene_id, script_payload["audio_blocks"])

        script_payload["audio_file"] = final_audio

        # =====================================================================
        # === BUILD SCENE RECORD ==============================================
        # =====================================================================

        preserved_time = headline.get("time") or headline.get("timestamp") if isinstance(headline, dict) else None

        scene = {
            "time": preserved_time or timestamp_iso,
            "source": source,
            "character": character,
            "topic": title or "—",
            "script": script_payload,    # ← full structured script
            "status": "compiled",
            "hash": scene_hash,
        }

        # === APPEND + TRIM ===
        existing.append(scene)
        if len(existing) > MAX_SCENES:
            existing = existing[-MAX_SCENES:]

        master = {"generated_at": timestamp_iso, "scenes": existing}
        json.dump(master, open(MASTER_PATH,"w"), indent=2)

        # === REFRESH DAILY COUNTS ===
        window_days = 60
        cutoff_counts = datetime.utcnow() - timedelta(days=window_days)

        def to_day_if_kept(s):
            if (s.get("status") == "system") or \
               ("Mock" in str(s.get("topic",""))) or \
               s.get("source") == "MockFeed":
                return None
            dt = to_naive_utc(s.get("time"))
            if not dt or dt < cutoff_counts:
                return None
            return dt.strftime("%Y-%m-%d")

        counts = Counter()
        for s in existing:
            day = to_day_if_kept(s)
            if day: counts[day] += 1

        dc_path = os.path.join(DATA_DIR, "daily_counts.json")
        json.dump(dict(sorted(counts.items())), open(dc_path,"w"), indent=2)
        print(f"[Dashboard] 🧮 daily_counts.json refreshed ({len(counts)} days)")

        # === SNAPSHOT (1000 newest) ===
        sorted_scenes = sorted(existing, key=lambda s: s.get("time",""), reverse=True)
        snap = {"generated_at": timestamp_iso, "scenes": sorted_scenes[:1000]}
        tmp = os.path.join(DATA_DIR,"scenes_snapshot.json.tmp")
        json.dump(snap, open(tmp,"w"), indent=2)
        os.replace(tmp, os.path.join(DATA_DIR,"scenes_snapshot.json"))
        print(f"[Dashboard] 🪶 Snapshot refreshed ({len(snap['scenes'])} scenes)")

        # === latest_scene.json ===
        json.dump(scene, open(LATEST_PATH,"w"), indent=2)

        # === WRITE TO SQLITE ===
        try:
            import time
            scene.setdefault("id", int(time.time()*1000))
            scene.setdefault("reply_to", None)
            conn = open_db(); c = conn.cursor()

            # script must be stored as JSON string
            scene_for_db = scene.copy()
            scene_for_db["script"] = json.dumps(scene["script"])
            scene_for_db["characters"] = json.dumps([scene.get("character","Chip")])

            c.execute("""
                INSERT OR REPLACE INTO scenes
                (id,time,character,topic,source,script,status,reply_to,characters)
                VALUES (:id,:time,:character,:topic,:source,:script,:status,:reply_to,:characters)
            """, scene_for_db)

            conn.commit(); conn.close()

        except Exception as e:
            print(f"[DB] ⚠️ Error persisting scene: {e}")

        from backend.script_engine.unreal_exporter import export_unreal_package
        export_unreal_package(script_payload)

        print(f"[Compiler] ✅ Scene compiled → {title}")

        return scene

    except Exception as e:
        print("[Compiler] Error:", e)



# =====================================================================
# === CLI / AUTO MODE ================================================
# =====================================================================

if __name__ == "__main__":
    import argparse, sys
    p = argparse.ArgumentParser()
    p.add_argument("--headline", required=True)
    p.add_argument("--source", default="manual")
    p.add_argument("--character", default="chip")

    args = p.parse_args()
    compile_scene(args.headline, args.source, args.character)
