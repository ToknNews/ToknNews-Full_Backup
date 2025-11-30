import os, json, hashlib, sqlite3, textwrap, re
from datetime import datetime, timedelta, timezone
from collections import Counter
from toknnews_scene_compiler_v1_8_studio_feedback import generate_scene
from script_engine.script_engine_v3 import generate_script

# === CONFIG ===
DATA_DIR = "/var/www/toknnews/data"
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
MASTER_PATH = os.path.join(DATA_DIR, "scenes.json")
LATEST_PATH = os.path.join(DATA_DIR, "latest_scene.json")
DB_PATH = os.path.join(DATA_DIR, "toknnews.db")
MAX_SCENES = 10000

os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

def strip_html(s):
    if not s: return ""
    s = re.sub(r'<[^>]+>', '', s)
    s = re.sub(r'https?://\S+', '', s)
    s = re.sub(r'\b\S+\.(jpg|jpeg|png|gif|webp|svg)\b', '', s, flags=re.IGNORECASE)
    s = re.sub(r'\s+', ' ', s).strip()
    return s[:1000]

# === LOAD RSS HEADLINES ===
def load_rss_headlines(path="/var/www/toknnews/data/raw/rss_latest.json", limit=500):
    if not os.path.exists(path): return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        elif not isinstance(data, list):
            print("[RSS Loader] ⚠️ Unexpected data structure"); return []
    except Exception as e:
        print(f"[RSS] Error loading {path}: {e}"); return []

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
            print(f"[RSS Loader] ⚠️ Skipped bad item: {e}"); continue
    return scenes

# === DB ===
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

def generate_anchor_script(enriched):
    """
    Small bridge wrapper to call Script Engine v3.
    Returns a script block dict:
    {
      "chip_intro": ...,
      "primary_section": ...,
      "secondary_section": ...,
      "chip_outro": ...
    }
    """
    try:
        return generate_script(enriched)
    except Exception as e:
        return {"error": f"Script engine failed: {e}"}

# === MAIN COMPILER ===
def compile_scene(headline, source="manual", character="chip"):
    try:
        now_et = datetime.now(timezone(timedelta(hours=-5)))
        timestamp_iso = now_et.isoformat()

        # Determine title + hash
        if isinstance(headline, dict):
            title = headline.get("topic") or headline.get("title") or headline.get("headline") or ""
        else:
            title = str(headline)
        scene_hash = hashlib.md5(title.encode()).hexdigest()

        # Load existing scenes (limit dedupe to past 24 hours)
        existing = []
        recent_hashes = set()
        if os.path.exists(MASTER_PATH):
            try:
                existing = json.load(open(MASTER_PATH)).get("scenes", [])
                now = datetime.utcnow()
                cutoff = now - timedelta(hours=24)

                for s in existing:
                    t = s.get("timestamp") or s.get("time")
                    h = s.get("hash")

                    # Only include hashes from the past 24h with valid timestamp
                    if h and t:
                        try:
                            ts = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                            if ts >= cutoff:
                                recent_hashes.add(h)
                        except Exception:
                            continue
            except Exception:
                pass

        # --- Deduplicate against last 7 days (normalize timestamps) ---
        def to_naive_utc(ts_str):
            try:
                dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
                if dt.tzinfo:
                    dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
                return dt
            except Exception:
                return None

        # --- Deduplicate against last 24 hours (per source + title) ---
        cutoff = datetime.utcnow() - timedelta(hours=24)

        recent_hashes = set()
        for s in existing:
            t = s.get("time")
            if not t:
                continue
            try:
                dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                if dt >= cutoff:
                    h = s.get("hash")
                    if h:
                        recent_hashes.add(h)
            except Exception:
                continue

        # Build a hash using both source and title so cross-posts aren't filtered out
        scene_hash = hashlib.md5(f"{source}:{title}".encode()).hexdigest()

        if scene_hash in recent_hashes:
            print("[SKIP] duplicate headline already exists in last-24-hour window")
            return

        # Build scene (preserve feed timestamp if provided)
        preserved_time = headline.get("time") or headline.get("timestamp") if isinstance(headline, dict) else None
        scene = {
            "script_block": generate_anchor_script(headline),
            "time": preserved_time or timestamp_iso,
            "source": source,
            "character": character,
            "topic": title or "—",
            "script": f"{character.upper()} reacts to: {title or '—'}",
            "status": "compiled",
            "hash": scene_hash,
        }

        scene["timestamp"] = scene.get("time")

        # Append, trim, write master
        existing.append(scene)
        if len(existing) > MAX_SCENES:
            existing = existing[-MAX_SCENES:]
        master = {"generated_at": timestamp_iso, "scenes": existing}
        json.dump(master, open(MASTER_PATH,"w"), indent=2)

        # --- Refresh daily_counts.json (non-system, recent window) ---
        window_days = 60
        cutoff_counts = datetime.utcnow() - timedelta(days=window_days)

        def to_day_if_kept(s):
            # drop mock/system or very old
            if (s.get("status") == "system") or ("Mock" in str(s.get("topic","")) or s.get("source") == "MockFeed"):
                return None
            dt = to_naive_utc(s.get("time"))
            if not dt or dt < cutoff_counts:
                return None
            return dt.strftime("%Y-%m-%d")

        counts = Counter()
        for s in existing:
            day = to_day_if_kept(s)
            if day:
                counts[day] += 1

        dc_path = os.path.join(DATA_DIR, "daily_counts.json")
        json.dump(dict(sorted(counts.items())), open(dc_path,"w"), indent=2)
        print(f"[Dashboard] 🧮 daily_counts.json refreshed ({len(counts)} days, window={window_days}d)")

        # Refresh snapshot (1000 newest, newest first)
        sorted_scenes = sorted(existing, key=lambda s: s.get("time",""), reverse=True)
        snap = {"generated_at": timestamp_iso, "scenes": sorted_scenes[:1000]}
        tmp = os.path.join(DATA_DIR,"scenes_snapshot.json.tmp")
        json.dump(snap, open(tmp,"w"), indent=2)
        os.replace(tmp, os.path.join(DATA_DIR,"scenes_snapshot.json"))
        print(f"[Dashboard] 🪶 Snapshot refreshed ({len(snap['scenes'])} scenes, newest first)")

        # Latest scene file
        json.dump(scene, open(LATEST_PATH,"w"), indent=2)

        # Persist to sqlite
        try:
            import time
            scene.setdefault("id", int(time.time()*1000))
            scene.setdefault("reply_to", None)
            conn = open_db(); c = conn.cursor()
            scene["characters"] = json.dumps(scene.get("characters", []))
            c.execute("""INSERT OR REPLACE INTO scenes
                         (id,time,character,topic,source,script,status,reply_to,characters)
                         VALUES (:id,:time,:character,:topic,:source,:script,:status,:reply_to,:characters)""",
                      scene)
            conn.commit(); conn.close()
        except Exception:
            print(f"[OK] Scene compiled and added ({len(existing)} total)")

        # Broadcast narrative (does not affect dashboard)
        generate_narrative_prompt(scene)

        # === Update persistent daily_tally.json (for chart) ===
        try:
            tally_path = os.path.join(DATA_DIR, "daily_tally.json")
            today = datetime.utcnow().date().isoformat()
            tally = {}
            if os.path.exists(tally_path):
                with open(tally_path, "r") as f:
                    tally = json.load(f)
            tally[today] = tally.get(today, 0) + 1
            tmp_path = tally_path + ".tmp"
            with open(tmp_path, "w") as f:
                json.dump(dict(sorted(tally.items())), f, indent=2)
            os.replace(tmp_path, tally_path)
            print(f"[Dashboard] 📊 daily_tally.json updated ({len(tally)} days)")
        except Exception as e:
            print(f"[Dashboard] ⚠️ Could not update daily_tally.json: {e}")

    except Exception as e:
        print("[Compiler] Error:", e)

# === Narrative (Sora) ===
def generate_narrative_prompt(scene_dict):
    try:
        narrative = generate_scene(sentiment="neutral",
                                   current_topic=scene_dict.get("topic"),
                                   next_topic=None)
        narrative = strip_html(narrative)
        json.dump({
            "generated_at": scene_dict.get("time"),
            "topic": scene_dict.get("topic"),
            "narrative": narrative
        }, open("/var/www/toknnews/data/latest_narrative.json","w"), indent=2)
        print(f"[Broadcast] Generated narrative for {scene_dict.get('topic','(unknown)')}")
    except Exception as e:
        print("[Broadcast] Narrative generation skipped:", e)

# === CLI / AUTO ===
if __name__ == "__main__":
    import argparse, sys
    p = argparse.ArgumentParser()
    p.add_argument("--headline", required=True)
    p.add_argument("--source", default="manual")
    p.add_argument("--character", default="chip")

    if len(sys.argv) == 1:
        print("[Auto-Mode] No CLI args detected — compiling RSS headlines instead.")
        rss = load_rss_headlines()
        if not rss:
            # heartbeat placeholder only if truly nothing to compile
            hb = {
                "time": datetime.utcnow().isoformat(),
                "source": "ToknNews",
                "character": "Chip",
                "topic": "[SYSTEM] Scheduled Ingestion Cycle",
                "script": "System heartbeat placeholder — no new headlines to compile.",
                "status": "system",
                "hash": hashlib.md5(b"[SYSTEM] Scheduled Ingestion Cycle").hexdigest()
            }
            json.dump(hb, open("/var/www/toknnews/data/latest_scene.json","w"), indent=2)
            json.dump({"generated_at": hb["time"], "topic": hb["topic"], "narrative": hb["script"]},
                      open("/var/www/toknnews/data/latest_narrative.json","w"), indent=2)
            print("[System] 🩺 Wrote placeholder heartbeat scene.")
            sys.exit(0)

        for s in rss:
            try:
                compile_scene(headline=s,
                              source=s.get("source","RSS"),
                              character=s.get("character","Chip"))
            except Exception as e:
                print(f"[Auto-Mode] Error compiling {s.get('topic','?')}: {e}")
        sys.exit(0)

    args = p.parse_args()
    compile_scene(args.headline, args.source, args.character)
