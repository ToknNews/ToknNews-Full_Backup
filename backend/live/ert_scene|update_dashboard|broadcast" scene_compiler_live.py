--- scene_compiler_live.py	2025-11-04 22:02:01.405385608 +0000
+++ toknnews_scene_compiler_v1_8_studio_feedback.py	2025-11-05 14:31:02.338799497 +0000
@@ -1,212 +1,161 @@
+cd /var/www/toknnews/modules
+cat > toknnews_scene_compiler_v1_8_studio_feedback.py <<'PY'
 #!/usr/bin/env python3
-# TOKNNews Scene Compiler v2.0
-# Unified, future-ready scene compiler for ChipStack / TOKNNews
-
-import os, json, datetime, hashlib, sqlite3
-
-# === CONFIG ===
-DATA_DIR = "/var/www/toknnews/data"
-ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")
-MASTER_PATH = os.path.join(DATA_DIR, "scenes.json")
-LATEST_PATH = os.path.join(DATA_DIR, "latest_scene.json")
-DB_PATH = os.path.join(DATA_DIR, "toknnews.db")
-MAX_SCENES = 10000  # keep latest n scenes in master file
-
-os.makedirs(DATA_DIR, exist_ok=True)
-os.makedirs(ARCHIVE_DIR, exist_ok=True)
-# === LOAD RSS HEADLINES ===
-def load_rss_headlines(path="/var/www/toknnews/data/raw/rss_latest.json", limit=50):
-    """load parsed RSS headlines and convert to scene dicts"""
-    if not os.path.exists(path):
-        return []
+# =========================================================
+# TOKNNews Scene Compiler v1.8 (Studio + Feedback Ready)
+# =========================================================
+# Generates Chip studio scenes with:
+#  • Dialogue-first structure for Sora lipsync
+#  • Stable studio lighting and gestures
+#  • Live vocabulary from chip_vocabulary.json
+#  • Sentiment bias & hijinx
+#  • Hooks for language learning and viewer feedback
+# =========================================================
+import os, random, textwrap, json
+from chip_vocabulary_loader import load_live_vocab
+
+COMPILER_VERSION = "1.8-studio-feedback"
+SUPPORTED_FEATURES = [
+    "dialogue_first", "studio_env", "sentiment_bias",
+    "hijinx", "learning_hook", "viewer_feedback"
+]
+
+# ---------------------------------------------------------
+#  Feedback hook
+# ---------------------------------------------------------
+FEEDBACK_PATH = "/var/www/toknnews/data/scene_feedback.json"
+
+def load_viewer_feedback():
+    """
+    Reads aggregated viewer reactions.
+    Expected JSON format:
+      {"likes":123,"dislikes":45,"positive_comments":67,"negative_comments":10}
+    Returns influence score between -1 and 1.
+    """
     try:
-        with open(path, "r") as f:
-            data = json.load(f)
+        if os.path.exists(FEEDBACK_PATH):
+            data = json.load(open(FEEDBACK_PATH))
+            score = (
+                data.get("likes",0)
+                - data.get("dislikes",0)
+                + 0.5*(data.get("positive_comments",0)
+                - data.get("negative_comments",0))
+            )
+            total = max(
+                data.get("likes",0)
+                + data.get("dislikes",0)
+                + data.get("positive_comments",0)
+                + data.get("negative_comments",0), 1
+            )
+            return max(min(score/total, 1), -1)
     except Exception:
-        return []
-
-    scenes = []
-    for item in data[:limit]:
-        title = item.get("title", "").strip()
-        if not title:
-            continue
-        scenes.append({
-            "time": datetime.datetime.utcnow().isoformat(),
-            "character": "Chip",
-            "topic": title,
-            "source": item.get("source", "RSS"),
-            "script": item.get("summary", "")[:300],
-            "status": "pending",
-            "reply_to": None,
-            "characters": "Chip",
-            "hash": hashlib.md5(title.encode()).hexdigest()
-        })
-    return scenes
-
-
-def open_db():
-    """open or create sqlite db"""
-    conn = sqlite3.connect(DB_PATH)
-    c = conn.cursor()
-    c.execute("""
-        CREATE TABLE IF NOT EXISTS scenes (
-            id TEXT PRIMARY KEY,
-            time TEXT,
-            character TEXT,
-            topic TEXT,
-            source TEXT,
-            script TEXT,
-            status TEXT,
-            reply_to TEXT,
-            characters TEXT,
-            hash TEXT
-        )
-    """)
-    conn.commit()
-    return conn
-
-
-def compile_scene(headline: str, source: str = "unknown", character: str = "chip"):
-    """Create and persist a unified scene object"""
-    from datetime import datetime, timezone, timedelta
-
-    # Convert to Eastern Time (UTC-5) — adjust automatically if DST matters later
-    eastern = timezone(timedelta(hours=-5))
-    now = datetime.now(eastern)
-    timestamp_iso = now.isoformat()
-
-    # === build base scene (preserve original timestamps if available) ===
-    preserved_time = None
-    if isinstance(headline, dict):
-        preserved_time = headline.get("time") or headline.get("timestamp")
-
-    scene = {
-        "time": preserved_time or timestamp_iso,  # keep real time if provided
-        "source": source,
-        "character": character,
-        "topic": headline if isinstance(headline, str) else headline.get("headline") or headline.get("title", "—"),
-        "script": f"{character.upper()} reacts to: {headline if isinstance(headline, str) else headline.get('headline') or headline.get('title', '—')}",
-        "status": "compiled"
-}
+        pass
+    return 0.0  # neutral if no data
 
-    # sanitize text fields for safe JSON (replace curly/smart quotes)
-    for key in ("topic", "script"):
-        scene[key] = (
-            str(scene[key])
-            .replace("’", "'")
-            .replace("‘", "'")
-            .replace("“", '"')
-            .replace("”", '"')
-            .replace("–", "-")
-            .replace("—", "-")
-            .strip()
-        )
-
-    # === deduplicate by headline hash ===
-    scene_hash = hashlib.md5(headline.encode()).hexdigest()
-    scene["hash"] = scene_hash
-
-    # ensure existing_scenes always exists before dedupe
-    existing_scenes = []
-    if os.path.exists(MASTER_PATH):
-        try:
-            with open(MASTER_PATH, "r") as f:
-                existing_scenes = json.load(f).get("scenes", [])
-        except Exception:
-            existing_scenes = []
-
-    # skip duplicate headlines seen recently
-    recent_hashes = {s.get("hash") for s in existing_scenes[-20:]}
-    if scene_hash in recent_hashes:
-        print("[SKIP] duplicate headline recently compiled")
-        return scene
-
-    # === append and trim ===
-    existing_scenes.append(scene)
-    if len(existing_scenes) > MAX_SCENES:
-        existing_scenes = existing_scenes[-MAX_SCENES:]
-
-    # === rebuild daily counts ===
-    counts = {}
-    for s in existing_scenes:
-        day = s.get("time", "").split("T")[0]
-        if day:
-            counts[day] = counts.get(day, 0) + 1
-
-    daily_counts = [{"date": d, "count": c} for d, c in sorted(counts.items())]
-
-    # === write archive (by day) ===
-    day_key = now.strftime("%Y-%m-%d")
-    archive_path = os.path.join(ARCHIVE_DIR, f"{day_key}.json")
-    day_scenes = [s for s in existing_scenes if str(s.get("time", "")).startswith(day_key)]
-    with open(archive_path, "w") as af:
-        json.dump(day_scenes, af, indent=2)
-
-    # === write master json ===
-    master = {
-        "generated_at": timestamp_iso,
-        "scenes": existing_scenes,
-        "daily_counts": daily_counts,
+# ---------------------------------------------------------
+#  Language-learning hook (placeholder)
+# ---------------------------------------------------------
+def language_learning_hook(scene_text:str, sentiment:str):
+    """
+    Future integration point.
+    Can analyse generated scene text and sentiment to
+    update chip_vocabulary.json or external model.
+    """
+    pass
+
+# ---------------------------------------------------------
+#  Sentiment tone table
+# ---------------------------------------------------------
+SENTIMENT_TONES = {
+    "bullish": {
+        "manner": ["brightly","with upbeat confidence","with quick energy"],
+        "verbs": ["grins","proclaims","adds cheerfully"]
+    },
+    "bearish": {
+        "manner": ["with measured calm","dryly","quietly"],
+        "verbs": ["says","notes","remarks"]
+    },
+    "neutral": {
+        "manner": ["in a steady tone","professionally","evenly"],
+        "verbs": ["says","explains","adds"]
     }
-    with open(MASTER_PATH, "w") as mf:
-        json.dump(master, mf, indent=2)
-
-    # === write latest scene trigger ===
-    with open(LATEST_PATH, "w") as lf:
-        json.dump(scene, lf, indent=2)
-
-    # === persist to sqlite ===
-    if "id" not in scene:
-        import time
-        scene["id"] = int(time.time() * 1000)
-
-    scene.setdefault("reply_to", None)
-
-    try:
-        print("DEBUG scene keys:", list(scene.keys()))
-        conn = open_db()
-        c = conn.cursor()
-        scene["characters"] = json.dumps(scene.get("characters", []))
-        c.execute(
-            """INSERT OR REPLACE INTO scenes 
-               (id, time, character, topic, source, script, status, reply_to, characters)
-               VALUES (:id, :time, :character, :topic, :source, :script, :status, :reply_to, :characters)""",
-            scene,
-        )
-        conn.commit()
-        conn.close()
-    except Exception as e:
-        print("[WARN] SQLite write failed:", e)
+}
 
-    print(f"[OK] Scene compiled and added ({len(existing_scenes)} total)")
+# ---------------------------------------------------------
+#  Helper utilities
+# ---------------------------------------------------------
+def pick(v): return random.choice(v)
+
+def generate_chip_motion():
+    motions = [
+        "leaning forward behind the glass desk",
+        "resting his elbows on the counter",
+        "tapping the holographic desk for emphasis",
+        "straightening his notes",
+        "gesturing toward the right monitor",
+        "glancing briefly at the ticker wall",
+        "folding his hands calmly on the desk",
+        "nodding toward the prompter"
+    ]
+    return pick(motions)
+
+def generate_hijinx():
+    hijinx_lines = [
+        "A panel flickers; Chip sighs. “Guess someone shorted the lighting budget.”",
+        "The prompter lags; Chip raises an eyebrow. “Technical analysis at work.”",
+        "A faint buzz crosses the mic; Chip smirks. “Market feedback, literally.”"
+    ]
+    return pick(hijinx_lines)
+
+# ---------------------------------------------------------
+#  Dialogue generator using live vocab + sentiment
+# ---------------------------------------------------------
+def generate_anchor_dialogue(sentiment="neutral"):
+    feedback_bias = load_viewer_feedback()
+    # Adjust sentiment based on viewer reactions
+    if feedback_bias > 0.25:
+        sentiment = "bullish"
+    elif feedback_bias < -0.25:
+        sentiment = "bearish"
+
+    vocab = load_live_vocab()
+    verbs = vocab.get("market_verbs", []) or ["rallies","slides","rebounds","surges"]
+    sentiments = vocab.get("sentiment_phrases", []) or ["optimism returns","momentum builds","volatility spikes"]
+    transitions = vocab.get("transitions", []) or [
+        "In other news,","Meanwhile in the markets,","Across the industry,","Turning to the next story,"
+    ]
+
+    tone = SENTIMENT_TONES.get(sentiment, SENTIMENT_TONES["neutral"])
+    speak_verb = pick(tone["verbs"])
+    manner = pick(tone["manner"])
+
+    opener = f"Bitcoin {pick(verbs)} as traders digest fresh data"
+    mid = f"Analysts note that {pick(sentiments)} heading into mid-week trading"
+    transition = pick(transitions)
+    return opener, mid, transition, speak_verb, manner, sentiment
+
+# ---------------------------------------------------------
+#  Scene generator
+# ---------------------------------------------------------
+def generate_scene(sentiment="neutral"):
+    opener, mid, transition, speak_verb, manner, sentiment = generate_anchor_dialogue(sentiment)
+    seg1 = f"“{opener},” Chip {speak_verb} {manner}, {generate_chip_motion()}."
+    seg2 = f"The camera glides slightly closer as he continues: “{mid}.”"
+    hijinx = generate_hijinx() if random.random() < 0.15 else ""
+    seg3 = f"He adjusts his posture, staying composed behind the desk. “{transition} stay tuned for updates.”"
+
+    scene = " ".join(filter(None, [seg1, seg2, hijinx, seg3]))
+    scene = textwrap.fill(scene, width=100)
+    language_learning_hook(scene, sentiment)
     return scene
 
-
+# ---------------------------------------------------------
+#  CLI runner
+# ---------------------------------------------------------
 if __name__ == "__main__":
-    import argparse
-
-    parser = argparse.ArgumentParser()
-    parser.add_argument("--headline", required=True)
-    parser.add_argument("--source", default="manual")
-    parser.add_argument("--character", default="chip")
-    # === fallback: auto-ingest RSS if no args provided ===
-    import sys
-    if len(sys.argv) == 1:
-        print("[Auto-Mode] No CLI args detected — compiling RSS headlines instead.")
-        rss_scenes = load_rss_headlines()
-        if not rss_scenes:
-            print("[Auto-Mode] No RSS items found, exiting.")
-            sys.exit(0)
-        for rss_scene in rss_scenes:
-            try:
-                compile_scene(
-                    headline=rss_scene["topic"],
-                    source=rss_scene.get("source", "RSS"),
-                    character=rss_scene.get("character", "Chip")
-                )
-            except Exception as e:
-                print(f"[Auto-Mode] Error compiling {rss_scene.get('topic','?')}: {e}")
-        sys.exit(0)
-    args = parser.parse_args()
+    print(f"\n🎬 TOKNNews Scene Compiler {COMPILER_VERSION}\n")
+    for s in ["bullish","neutral","bearish"]:
+        print(f"\n--- {s.upper()} ---")
+        print(generate_scene(sentiment=s))
+    print("\n--- End of Scene ---\n")
 
-    compile_scene(args.headline, args.source, args.character)
