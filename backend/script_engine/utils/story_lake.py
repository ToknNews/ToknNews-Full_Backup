import json
from pathlib import Path

# ==========================================================
# STORY LAKE SHARDS (STORAGE LAYER)
# ==========================================================

STORY_DIR = Path("/opt/toknnews/data/stories")
STORY_DIR.mkdir(parents=True, exist_ok=True)

SHARDS = {
    "rss": STORY_DIR / "story_lake_rss.json",
    "onchain": STORY_DIR / "story_lake_onchain.json",
    "synth": STORY_DIR / "story_lake_synth.json",
    "gpt": STORY_DIR / "story_lake_gpt.json",
}

INDEX_PATH = STORY_DIR / "story_lake_index.json"

# ----------------------------------------------------------
# ENSURE ALL SHARD FILES EXIST (CRITICAL FIX)
# ----------------------------------------------------------

for path in list(SHARDS.values()) + [INDEX_PATH]:
    if not path.exists():
        path.write_text("[]")


# ==========================================================
# LOW-LEVEL FILE HELPERS
# ==========================================================

def _load(path: Path) -> list:
    try:
        return json.loads(path.read_text())
    except Exception:
        return []


def _write(path: Path, data: list):
    path.write_text(json.dumps(data, indent=2))


# ==========================================================
# SHARDED APPEND (SINGLE SOURCE OF TRUTH)
# ==========================================================

def append_story_sharded(story: dict):
    """
    Append a story to the correct shard AND update the global index.

    This is the ONLY function that should ever write to Story Lake.
    """

    source = story.get("source", "RSS")

    # -------------------------------
    # ROUTE TO SHARD BY SOURCE
    # -------------------------------
    if source == "moralis_stream":
        shard_key = "onchain"
    elif source == "onchain_synth_v1":
        shard_key = "synth"
    elif source == "gpt_ingest_v1":
        shard_key = "gpt"
    else:
        shard_key = "rss"

    shard_path = SHARDS[shard_key]

    # -------------------------------
    # WRITE STORY TO SHARD
    # -------------------------------
    shard_data = _load(shard_path)
    shard_data.append(story)
    _write(shard_path, shard_data)

    # -------------------------------
    # UPDATE GLOBAL INDEX
    # -------------------------------
    index = _load(INDEX_PATH)
    index.append({
        "id": story.get("tx_hash") or story.get("timestamp"),
        "source": source,
        "shard": shard_key,
        "timestamp": story.get("timestamp"),
        "domain": story.get("domain"),
        "importance": story.get("importance"),
    })
    _write(INDEX_PATH, index)


# ==========================================================
# UNIFIED READ (KNOWLEDGE LAYER)
# ==========================================================

def load_story_lake_all() -> list:
    """
    Load all stories across shards.
    Used ONLY by ranking, clustering, editorial logic.
    """
    stories = []
    for path in SHARDS.values():
        stories.extend(_load(path))
    return stories
