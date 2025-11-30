#!/usr/bin/env python3
"""
TOKNNews — Chip Vocabulary Loader v2.0
-------------------------------------
Loads, validates, and updates Chip’s live vocabulary
for use by compilers and studio renderers.
Supports hot reload + optional feedback weighting.
"""

import os, json, time

VOCAB_PATH = "/var/www/toknnews/data/chip_vocabulary.json"
DEFAULT_PATH = "/var/www/toknnews/modules/defaults/chip_vocabulary_default.json"
FEEDBACK_PATH = "/var/www/toknnews/data/scene_feedback.json"

EXPECTED_KEYS = [
    "moods", "camera_moves", "gestures", "motion_phrases",
    "energy_modifiers", "rhetorical_hooks", "update_policy"
]

_cache = {}
_last_loaded = 0


# ------------------------------------------------------------
# Utility Functions
# ------------------------------------------------------------
def _load_json(path: str) -> dict:
    """Read and parse JSON safely."""
    try:
        with open(path, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[Vocab] File not found: {path}")
    except json.JSONDecodeError as e:
        print(f"[Vocab] JSON error in {path}: {e}")
    except Exception as e:
        print(f"[Vocab] Unexpected error reading {path}: {e}")
    return {}


def _validate_vocab(vocab: dict) -> dict:
    """Ensure required sections exist; warn if missing."""
    missing = [k for k in EXPECTED_KEYS if k not in vocab]
    if missing:
        print(f"[Vocab] ⚠️ Missing keys: {missing}")
        for key in missing:
            vocab[key] = vocab.get(key, [])
    return vocab


def _merge_defaults(vocab: dict, default_vocab: dict) -> dict:
    """Fill missing fields from default baseline."""
    for key, val in default_vocab.items():
        if key not in vocab:
            vocab[key] = val
        elif isinstance(val, dict):
            vocab[key] = {**val, **vocab.get(key, {})}
    return vocab


def _apply_feedback_weights(vocab: dict) -> dict:
    """Optionally adjust tone weighting based on scene feedback."""
    if not os.path.exists(FEEDBACK_PATH):
        return vocab
    try:
        feedback = _load_json(FEEDBACK_PATH)
        likes = feedback.get("likes", 0)
        dislikes = feedback.get("dislikes", 0)
        if likes + dislikes == 0:
            return vocab
        ratio = likes / (likes + dislikes)
        bias = round((ratio - 0.5) * 2, 2)  # range -1 → +1
        mood = "bullish" if bias > 0 else "bearish"
        vocab.setdefault("weights", {})[mood] = abs(bias)
        print(f"[Vocab] Adjusted mood weighting from feedback → {mood} ({bias:+.2f})")
    except Exception as e:
        print(f"[Vocab] Feedback weighting skipped: {e}")
    return vocab


def _summarize(vocab: dict):
    """Print short summary for observability."""
    try:
        moods = vocab.get("moods", {})
        total_verbs = sum(len(v.get("verbs", [])) for v in moods.values())
        total_adjs = sum(len(v.get("adjectives", [])) for v in moods.values())
        cams = len(vocab.get("camera_moves", []))
        print(f"[Vocab] ✅ Loaded {len(moods)} moods | {total_verbs} verbs | "
              f"{total_adjs} adjectives | {cams} camera moves")
    except Exception:
        pass


# ------------------------------------------------------------
# Public Loader
# ------------------------------------------------------------
def load_live_vocab(force_reload: bool = False) -> dict:
    """Main loader with caching, validation, and hot reload."""
    global _cache, _last_loaded
    try:
        if not os.path.exists(VOCAB_PATH):
            print("[Vocab] Creating baseline vocabulary from defaults.")
            _cache = _load_json(DEFAULT_PATH)
            _cache = _validate_vocab(_cache)
            _summarize(_cache)
            return _cache

        mtime = os.path.getmtime(VOCAB_PATH)
        if force_reload or mtime != _last_loaded:
            vocab = _load_json(VOCAB_PATH)
            if not vocab:
                vocab = _load_json(DEFAULT_PATH)
            default_vocab = _load_json(DEFAULT_PATH)
            vocab = _merge_defaults(vocab, default_vocab)
            vocab = _validate_vocab(vocab)
            vocab = _apply_feedback_weights(vocab)
            _cache = vocab
            _last_loaded = mtime
            _summarize(vocab)
        return _cache
    except Exception as e:
        print(f"[Vocab] Critical error: {e}")
        return _cache or {}


# ------------------------------------------------------------
# CLI Test Harness
# ------------------------------------------------------------
if __name__ == "__main__":
    v = load_live_vocab(force_reload=True)
    print(json.dumps(v, indent=2)[:800] + "\n...")
