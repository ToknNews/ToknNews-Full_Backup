#!/usr/bin/env python3
# =========================================================
# TOKNNews Scene Compiler v1.9 — Semantic Aware Edition
# =========================================================
# Generates Chip studio scenes with:
#  • Immediate, high-energy dialogue (no preamble)
#  • Smart theme classification per line
#  • Dynamic verbs, gestures, and camera cues
#  • Strong quote discipline and pacing
# =========================================================

import os, json, textwrap, random
from chip_vocabulary_loader import load_live_vocab
from schema_validator import validate_schema
from compile_safety import atomic_write, log_compile, update_continuity, validate_scene
validate_schema()

# --- Load global vocabulary once ---
VOCAB = load_live_vocab()

SEMANTIC_MAP_PATH = "/var/www/toknnews/data/semantic_map.json"

# =========================================================
# Semantic Classifier
# =========================================================
def classify_theme(text: str) -> str:
    """Simple keyword-based theme classifier."""
    t = text.lower()

    # Load semantic map if available
    try:
        with open(SEMANTIC_MAP_PATH, "r") as f:
            mapping = json.load(f)
        for mood, keywords in mapping.items():
            if any(k in t for k in keywords):
                return mood
    except Exception:
        pass

    # Fallback classification
    if any(k in t for k in ["surge", "rally", "breaks", "record", "rockets"]):
        return "bullish"
    if any(k in t for k in ["fall", "drop", "crash", "slump", "liquidation"]):
        return "bearish"
    if any(k in t for k in ["regulation", "lawsuit", "sec", "hearing", "ban"]):
        return "serious"
    if any(k in t for k in ["launch", "announcement", "update", "token"]):
        return "neutral"
    return "neutral"


# =========================================================
# Helper: Safe JSON loader
# =========================================================
def _load_json(path: str) -> dict:
    """Safely load and parse JSON file."""
    try:
        if os.path.exists(path):
            with open(path, "r") as f:
                return json.load(f)
    except Exception as e:
        print(f"[JSON] Could not load {path}: {e}")
    return {}

# =========================================================
# Transition selector for contextual segues
# =========================================================
def choose_transition(current_topic: str, next_topic: str = None) -> str:
    """
    Chooses a natural segue line based on topic similarity.
    If the next topic shares a keyword, use a soft handoff;
    otherwise, use a strong pivot.
    """
    soft_links = [
        "staying on that theme,",
        "continuing with the trend,",
        "keeping the focus on",
        "following up on that,",
        "still in the crypto space,"
    ]
    hard_pivots = [
        "turning to a different story,",
        "on another front,",
        "outside of crypto,",
        "shifting gears,",
        "meanwhile elsewhere,"
    ]

    if not next_topic:
        return random.choice(["that’s the latest for now,", "more updates soon,"])

    current_tokens = set(current_topic.lower().split())
    next_tokens = set(next_topic.lower().split())
    overlap = len(current_tokens.intersection(next_tokens))
    related_terms = {"bitcoin", "crypto", "ethereum", "markets", "ai", "fed", "etf"}

    related = (
        overlap >= 2
        or (current_tokens & related_terms)
        and (next_tokens & related_terms)
    )

    if related:
        return random.choice(soft_links)
    return random.choice(hard_pivots)

# =========================================================
# Core Scene Generator
# =========================================================
def generate_scene(sentiment="neutral", current_topic=None, next_topic=None):
    """
    Context-aware scene builder with continuity memory, emotional carryover,
    and Sora block schema export.
    """
    # === Load memory from last scene ===
    memory_path = "/var/www/toknnews/data/last_scene.json"
    last_topic, last_sentiment = None, "neutral"
    if os.path.exists(memory_path):
        try:
            with open(memory_path, "r") as m:
                mem = json.load(m)
                last_topic = mem.get("last_topic")
                last_sentiment = mem.get("last_sentiment", "neutral")
        except Exception:
            pass

    # === Emotional carryover ===
    mood_shift = {"bullish": 1, "neutral": 0, "bearish": -1}
    shift = mood_shift.get(sentiment, 0) + mood_shift.get(last_sentiment, 0)
    if shift > 1: sentiment = "bullish"
    elif shift < -1: sentiment = "bearish"
    else: sentiment = "neutral"

    # === Base Setup ===
    parts = []
    schema = _load_json("/var/www/toknnews/data/scene_block_schema.json") or {}
    framing = schema.get("block_structure", {}).get("framing", {})
    dialogue_block = schema.get("block_structure", {}).get("dialogue", {})
    segue_block = schema.get("block_structure", {}).get("segue", {})

    parts.append(framing.get("description", ""))

    # === Opening line (immediate speech) ===
    delivery_open = random.choice(VOCAB["moods"].get(sentiment, {}).get("verbs", ["reports"]))
    camera_open = random.choice(VOCAB.get("camera_moves", ["camera steady center"]))
    gesture_open = random.choice(VOCAB.get("gestures", ["leans forward"]))
    opener_line = f"“{cap_words(current_topic or 'Markets open mixed across crypto.', 18)}!” Chip {delivery_open} as {camera_open} and {gesture_open}."
    parts.append(opener_line)

    # === Generate dialogue lines from feed ===
    body_text = ""
    feed_path = "/var/www/toknnews/data/raw/rss_latest.json"
    if os.path.exists(feed_path):
        try:
            with open(feed_path, "r") as f:
                data = json.load(f)
            items = data.get("items", data)
            body_text = " ".join(
                [(it.get("summary", "") or it.get("description", "")) for it in items[:5] if isinstance(it, dict)]
            )
        except Exception:
            pass

    analysis_lines = [s.strip() for s in body_text.split(".") if len(s.split()) > 4][:4]
    if not analysis_lines:
        analysis_lines = [
            "Traders watch key resistance levels",
            "Institutional flows continue",
            "Volatility holds near support",
            "Market sentiment remains mixed"
        ]

    # === Line-by-line semantic phrasing ===
    for line in analysis_lines:
        theme = classify_theme(line)
        mood = VOCAB["moods"].get(theme, VOCAB["moods"].get(sentiment, {}))
        verb = random.choice(mood.get("verbs", ["reports"]))
        adj = random.choice(mood.get("adjectives", ["focused"]))
        spoken = cap_words(line, 18)
        parts.append(f"“{spoken},” Chip {verb} with {adj} precision.")

    # === Contextual segue generation ===
    segue_phrase = choose_transition(current_topic or "", next_topic or "")
    closing_move = random.choice(VOCAB.get("motion_phrases", ["camera pulls back slightly"]))
    closing_gesture = random.choice(VOCAB.get("gestures", ["folds his notes neatly"]))
    if next_topic:
        parts.append(f"“{segue_phrase} {next_topic.split()[0]} next,” Chip announces.")
    else:
        parts.append(f"“{segue_phrase} stay tuned for more updates,” Chip concludes.")

    parts.append(f"{closing_gesture.capitalize()}, {closing_move}.")

    # === Memory writeback ===
    try:
        with open(memory_path, "w") as m:
            json.dump({"last_topic": current_topic, "last_sentiment": sentiment}, m, indent=2)
    except Exception as e:
        print("[Memory] Could not write memory:", e)

    # === Join + timing metadata ===
    scene_text = " ".join(parts)
    scene_text = textwrap.fill(scene_text, width=100)
    word_count = len(scene_text.split())
    est_runtime = round(word_count / (160 / 60), 1)
    scene_text += f"\n\n# Estimated runtime: {est_runtime}s at Chip cadence ({word_count} words)."

    # === Export Sora-ready schema ===
    sora_blocks = [
        {"block": "framing", "duration": framing.get("duration", 0.01), "text": framing.get("description", "")},
        {"block": "dialogue", "duration": dialogue_block.get("duration", 14.9), "text": " ".join(parts[1:-2])},
        {"block": "segue", "duration": segue_block.get("duration", 10.0), "text": " ".join(parts[-2:])}
    ]

    # === Validate and write safely ===
    try:
        validate_scene(sora_blocks)
        atomic_write("/var/www/toknnews/data/latest_scene_blocks.json", sora_blocks)
        print("[SafeWrite] ✅ Scene blocks validated and saved atomically.")
    except Exception as e:
        print(f"[SafeWrite] ❌ Validation failed: {e}")

    # === Log compile + update continuity ===
    try:
        log_compile(current_topic or "unknown", sentiment, next_topic or "", est_runtime, ok=True)
        update_continuity(last_topic, current_topic, next_topic, sentiment, segue_phrase)
        print(f"[Continuity] {last_topic} → {current_topic} → {next_topic} | Tone: {sentiment}")
    except Exception as e:
        log_compile(current_topic or "unknown", sentiment, next_topic or "", est_runtime, ok=False, err=str(e))
        print(f"[Continuity] Logging failed: {e}")

    # === Update heartbeat ===
    from heartbeat_updater import update_heartbeat
    try:
        update_heartbeat(current_topic or "unknown", sentiment, est_runtime, status="success")
    except Exception as e:
        update_heartbeat(current_topic or "unknown", sentiment, est_runtime, status="error", error=str(e))

    # === Telegram alert trigger (errors only) ===
    try:
        from telegram_alerts import alert_from_heartbeat
        compile_status = "success"   # define status here or use logic later
        if compile_status != "success":  # only send alert on failure
            alert_from_heartbeat()
    except Exception as e:
        print(f"[Telegram] Skipped alert send: {e}")

    return scene_text


# =========================================================
# Utility
# =========================================================
def cap_words(text: str, max_words: int) -> str:
    words = text.split()
    return " ".join(words[:max_words]).rstrip(",; ")

# =========================================================
# CLI Runner
# =========================================================
if __name__ == "__main__":
    print(f"\n🎬 TOKNNews Scene Compiler v1.9 — Semantic Aware\n")
    sample_scene = generate_scene(
        sentiment="bullish",
        current_topic="Bitcoin rockets to new highs amid ETF frenzy",
        next_topic="Ethereum prepares for next network upgrade"
    )
    print(sample_scene)
    print("\n--- End of Scene ---\n")
