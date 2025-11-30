
#!/usr/bin/env python3
"""
TOKNNews — Scene Compiler (Dev Sandbox Clean Build)
---------------------------------------------------
This version is isolated for sandbox testing and safe experimentation.
It preserves all production compiler functionality while redirecting
writes to `/var/www/toknnews/devdata/` instead of `/data/`.

Includes:
 - MiniLM semantic recall (Chip’s contextual memory)
 - Dual narrative systems (Sora + Sandbox)
 - Safe sandbox JSON writes
 - Archive toggle for versioned outputs
"""

# -------------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------------
import os, json, hashlib, sqlite3, textwrap, re, numpy as np
from datetime import datetime, timedelta, timezone
from collections import Counter
from sentence_transformers import SentenceTransformer  # <-- REQUIRED for MiniLM recall

# try to load the real scene generator; fall back to stub if not found
try:
    from toknnews_scene_compiler_v1_8_studio_feedback import generate_scene
except ModuleNotFoundError:
    def generate_scene(sentiment="neutral", current_topic="", next_topic=None):
        """Fallback generator used only in sandbox if main module missing."""
        return f"[Stub Scene Generator] ({sentiment}) {current_topic}"

# -------------------------------------------------------------------
# CONFIGURATION
# -------------------------------------------------------------------
DATA_DIR = "/var/www/toknnews/data"
DEV_DIR  = "/var/www/toknnews/devdata"
ARCHIVE_DIR = os.path.join(DEV_DIR, "archive")
MASTER_PATH = os.path.join(DEV_DIR, "scenes.json")
LATEST_PATH = os.path.join(DEV_DIR, "latest_scene.json")
DB_PATH = os.path.join(DEV_DIR, "toknnews.db")
MAX_SCENES = 10000

ENABLE_VERSIONED_ARCHIVE = False

os.makedirs(DEV_DIR, exist_ok=True)
os.makedirs(ARCHIVE_DIR, exist_ok=True)

# -------------------------------------------------------------------
# SANDBOX UTILS
# -------------------------------------------------------------------
def strip_html(s: str) -> str:
    """Remove HTML tags, URLs, and extra whitespace."""
    if not s:
        return ""
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"https?://\S+", "", s)
    s = re.sub(r"\b\S+\.(jpg|jpeg|png|gif|webp|svg)\b", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s+", " ", s).strip()
    return s[:1000]


# -------------------------------------------------------------------
# MINI-LM MODEL (LOCAL OFFLINE)
# -------------------------------------------------------------------
RECALL_DB = os.path.join(DEV_DIR, "memories.db")
recall_model = SentenceTransformer("all-MiniLM-L6-v2")


# -------------------------------------------------------------------
# RECALL CONTEXT (SEMANTIC MEMORY)
# -------------------------------------------------------------------
def recall_context(query_text: str, top_k: int = 3) -> str:
    """Fetch the most semantically similar past lines from memories.db."""
    if not os.path.exists(RECALL_DB):
        print(f"[Recall] ❌ No memory DB found at {RECALL_DB}")
        return ""

    conn = sqlite3.connect(RECALL_DB)
    cur = conn.cursor()
    cur.execute("SELECT text, embedding FROM memories WHERE embedding IS NOT NULL")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        print("[Recall] No memories with embeddings found.")
        return ""

    q_vec = np.array(recall_model.encode(query_text), dtype=np.float32)
    sims = []
    for text, emb_json in rows:
        try:
            emb = np.array(json.loads(emb_json), dtype=np.float32)
            sim = np.dot(q_vec, emb) / (np.linalg.norm(q_vec) * np.linalg.norm(emb))
            sims.append((sim, text))
        except Exception:
            continue

    sims.sort(reverse=True, key=lambda x: x[0])
    top = [t for _, t in sims[:top_k]]
    return "\n".join(f"- {t}" for t in top)


# -------------------------------------------------------------------
# DATABASE HELPERS
# -------------------------------------------------------------------
def open_db():
    """Open or create SQLite DB for compiled scenes."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS scenes(
            id TEXT PRIMARY KEY,
            time TEXT, character TEXT, topic TEXT,
            source TEXT, script TEXT, status TEXT,
            reply_to TEXT, characters TEXT, hash TEXT
        )
        """
    )
    return conn


# -------------------------------------------------------------------
# LOAD RSS HEADLINES (utility for auto mode)
# -------------------------------------------------------------------
def load_rss_headlines(path=f"{DATA_DIR}/raw/rss_latest.json", limit=500):
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r") as f:
            data = json.load(f)
        if isinstance(data, dict) and "items" in data:
            data = data["items"]
        elif not isinstance(data, list):
            print("[RSS Loader] ⚠️ Unexpected data structure")
            return []
    except Exception as e:
        print(f"[RSS] Error loading {path}: {e}")
        return []

    scenes = []
    for item in data[:limit]:
        try:
            title = (item.get("title") or item.get("headline") or "").strip()
            if not title:
                continue
            summary = (item.get("summary", "") + " " + item.get("description", "")).strip()
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
            print(f"[RSS Loader] ⚠️ Skipped bad item: {e}")
            continue
    return scenes


# -------------------------------------------------------------------
# COMPILE SCENE (MAIN FUNCTION)
# -------------------------------------------------------------------
def compile_scene(headline, source="manual", character="chip"):
    """Compile a scene: dedupe, log, persist, and trigger narrative generation."""
    try:
        now_et = datetime.now(timezone(timedelta(hours=-5)))
        timestamp_iso = now_et.isoformat()

        # Determine title + hash
        title = ""
        if isinstance(headline, dict):
            title = headline.get("topic") or headline.get("title") or headline.get("headline") or ""
        else:
            title = str(headline)
        scene_hash = hashlib.md5(title.encode()).hexdigest()

        # Load existing scenes for deduplication
        existing = []
        if os.path.exists(MASTER_PATH):
            try:
                existing = json.load(open(MASTER_PATH)).get("scenes", [])
            except Exception:
                existing = []

        cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_hashes = set()
        for s in existing:
            try:
                t = s.get("time")
                if not t:
                    continue
                dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                if dt >= cutoff:
                    h = s.get("hash")
                    if h:
                        recent_hashes.add(h)
            except Exception:
                continue

        scene_hash = hashlib.md5(f"{source}:{title}".encode()).hexdigest()
        if scene_hash in recent_hashes:
            print("[SKIP] duplicate headline already exists in last 24h")
            return

        # Build scene dict
        preserved_time = (
            headline.get("time") or headline.get("timestamp") if isinstance(headline, dict) else None
        )
        scene = {
            "time": preserved_time or timestamp_iso,
            "source": source,
            "character": character,
            "topic": title or "—",
            "script": f"{character.upper()} reacts to: {title or '—'}",
            "status": "compiled",
            "hash": scene_hash,
        }
        scene["timestamp"] = scene.get("time")

        # Append + trim
        existing.append(scene)
        if len(existing) > MAX_SCENES:
            existing = existing[-MAX_SCENES:]

        master = {"generated_at": timestamp_iso, "scenes": existing}
        json.dump(master, open(MASTER_PATH, "w"), indent=2)

        # Refresh daily_counts.json
        window_days = 60
        cutoff_counts = datetime.utcnow() - timedelta(days=window_days)
        def to_day_if_kept(s):
            if (s.get("status") == "system") or (
                "Mock" in str(s.get("topic", "")) or s.get("source") == "MockFeed"
            ):
                return None
            try:
                dt = datetime.fromisoformat(str(s.get("time")).replace("Z", "+00:00"))
                if dt < cutoff_counts:
                    return None
                return dt.strftime("%Y-%m-%d")
            except Exception:
                return None

        counts = Counter()
        for s in existing:
            d = to_day_if_kept(s)
            if d:
                counts[d] += 1

        dc_path = os.path.join(DEV_DIR, "daily_counts.json")
        json.dump(dict(sorted(counts.items())), open(dc_path, "w"), indent=2)

        # Snapshot
        sorted_scenes = sorted(existing, key=lambda s: s.get("time", ""), reverse=True)
        snap = {"generated_at": timestamp_iso, "scenes": sorted_scenes[:1000]}
        tmp = os.path.join(DEV_DIR, "scenes_snapshot.json.tmp")
        json.dump(snap, open(tmp, "w"), indent=2)
        os.replace(tmp, os.path.join(DEV_DIR, "scenes_snapshot.json"))

        # Persist to sqlite
        try:
            import time
            scene.setdefault("id", int(time.time() * 1000))
            scene.setdefault("reply_to", None)
            conn = open_db(); c = conn.cursor()
            scene["characters"] = json.dumps(scene.get("characters", []))
            c.execute(
                """INSERT OR REPLACE INTO scenes
                   (id,time,character,topic,source,script,status,reply_to,characters)
                   VALUES (:id,:time,:character,:topic,:source,:script,:status,:reply_to,:characters)""",
                scene,
            )
            conn.commit(); conn.close()
        except Exception as e:
            print(f"[Compiler] ⚠️ SQLite insert failed: {e}")

        # Trigger sandbox narrative
        generate_narrative_prompt_sandbox(scene)

    except Exception as e:
        print(f"[Compiler] ❌ Error in compile_scene: {e}")


# -------------------------------------------------------------------
# SORA / LIVE NARRATIVE
# -------------------------------------------------------------------
def generate_narrative_prompt(scene_dict):
    """Generate standard narrative for production / Sora-style rendering."""
    try:
        narrative = generate_scene(
            sentiment="neutral",
            current_topic=scene_dict.get("topic"),
            next_topic=None,
        )
        narrative = strip_html(narrative)
        json.dump(
            {
                "generated_at": scene_dict.get("time"),
                "topic": scene_dict.get("topic"),
                "narrative": narrative,
            },
            open("/var/www/toknnews/data/latest_narrative.json", "w"),
            indent=2,
        )
        print(f"[Broadcast] Generated Sora narrative for {scene_dict.get('topic','(unknown)')}")
    except Exception as e:
        print(f"[Broadcast] Narrative generation skipped: {e}")


# -------------------------------------------------------------------
# SANDBOX NARRATIVE
# -------------------------------------------------------------------
def generate_narrative_prompt_sandbox(scene_dict):
    """Generate sandbox narrative using recall context."""
    try:
        topic = scene_dict.get("topic") or ""
        past_lines = recall_context(topic)
        if past_lines:
            print(f"[Recall] Injecting {len(past_lines.splitlines())} memory lines for context.")
        else:
            print("[Recall] No similar past lines found.")

        context_text = f"Chip’s previous commentary:\n{past_lines}\n\nNew headline: {topic}\n"
        narrative = generate_scene(sentiment="neutral", current_topic=context_text, next_topic=None)
        narrative = strip_html(narrative)

        sandbox_output = os.path.join(DEV_DIR, "latest_narrative.json")
        json.dump(
            {
                "generated_at": scene_dict.get("time"),
                "topic": scene_dict.get("topic"),
                "narrative": narrative,
            },
            open(sandbox_output, "w"),
            indent=2,
        )
        print(
            f"[Sandbox Broadcast] 🧩 Generated narrative for "
            f"{scene_dict.get('topic','(unknown)')} → {sandbox_output}"
        )

    except Exception as e:
        print(f"[Sandbox Broadcast] Narrative generation skipped: {e}")


# -------------------------------------------------------------------
# CLI / AUTO MODE
# -------------------------------------------------------------------
if __name__ == "__main__":
    import argparse, sys
    p = argparse.ArgumentParser()
    p.add_argument("--headline", required=True)
    p.add_argument("--source", default="manual")
    p.add_argument("--character", default="chip")

    args = p.parse_args()
    compile_scene(args.headline, args.source, args.character)
