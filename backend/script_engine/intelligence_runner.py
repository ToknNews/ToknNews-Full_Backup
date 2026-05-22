#!/usr/bin/env python3
"""
intelligence_runner.py — ToknNews Master Intelligence Orchestrator (v4)

Upgrades:
- Rolling clustering window (configurable)
- Cluster ranking + gating (LLM control)
- Narrative reuse penalty (SQLite narrative_usage)
- Chainstack numeric snapshot injection (episode-level numeric_context)
- Optional signal snapshot injection (episode-level signal_context)
- Canonical artifact bundle per run (+ latest symlink)
"""

from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

BASE_DIR = Path("/opt/toknnews")
DATA_DIR = BASE_DIR / "data"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
STORIES_DIR = DATA_DIR / "stories"
EPISODES_DIR = DATA_DIR / "episodes"

LEGACY_STORY_LAKE = STORIES_DIR / "story_lake.json"
LEGACY_REFINED_CLUSTERS = STORIES_DIR / "story_refined_clusters.json"
LEGACY_NARRATIVE_BRIEFS = STORIES_DIR / "narrative_briefs.json"
LEGACY_DIALOGUE_BLOCKS = STORIES_DIR / "dialogue_blocks.json"

PYTHON = "/usr/bin/env"
PYTHON_ARG = "python3"


# ============================================================
# ENV HELPERS
# ============================================================

def _env_int(name: str, default: int) -> int:
    try:
        return int(os.getenv(name, str(default)).strip())
    except Exception:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "1" if default else "0").strip().lower()
    return raw in ("1", "true", "yes", "y", "on")


# ============================================================
# FILE HELPERS
# ============================================================

def _atomic_write_json(path: Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(obj, indent=2))
    tmp.replace(path)


def _safe_load_json(path: Path) -> Any:
    return json.loads(path.read_text())


def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def _symlink_latest(latest: Path, target: Path) -> None:
    latest_tmp = latest.with_name(latest.name + "_tmp")
    if latest_tmp.exists() or latest_tmp.is_symlink():
        latest_tmp.unlink()
    latest_tmp.symlink_to(target, target_is_directory=True)

    if latest.exists() or latest.is_symlink():
        latest.unlink()
    latest_tmp.replace(latest)


def _run_subprocess(cmd: List[str]) -> None:
    subprocess.run(cmd, check=True)


# ============================================================
# NARRATIVE MEMORY PENALTY (Phase 2 - Layer 1)
# ============================================================

def _get_narrative_usage_map() -> Dict[str, tuple]:
    """
    Returns:
      novelty_hash -> (usage_count, last_used_ts)
    """
    from backend.runtime.sqlite_utils import connect_sqlite

    db_path = Path("/opt/toknnews/data/analytics.db")
    conn = connect_sqlite(str(db_path))
    cur = conn.cursor()
    cur.execute("SELECT novelty_hash, usage_count, last_used_ts FROM narrative_usage")
    rows = cur.fetchall()
    conn.close()

    usage: Dict[str, tuple] = {}
    for novelty_hash, usage_count, last_used_ts in rows:
        usage[novelty_hash] = (usage_count or 0, last_used_ts or 0)
    return usage


def _cluster_reuse_penalty(cluster: dict, usage_map: Dict[str, tuple]) -> float:
    stories = cluster.get("stories", [])
    penalty = 0.0
    now = time.time()

    for s in stories:
        capsule = s.get("fact_capsule") or {}
        novelty_hash = capsule.get("novelty_hash")
        if not novelty_hash:
            continue

        usage_count, last_used_ts = usage_map.get(novelty_hash, (0, 0))

        # recency penalty (last 48h)
        if last_used_ts and (now - last_used_ts) < (48 * 3600):
            penalty += 2.0

        # frequency penalty
        penalty += float(usage_count) * 0.5

    return penalty


# ============================================================
# STORY + WINDOW
# ============================================================

def _load_story_lake() -> List[dict]:
    if not LEGACY_STORY_LAKE.exists():
        raise FileNotFoundError("story_lake.json missing")
    stories = _safe_load_json(LEGACY_STORY_LAKE)
    return [s for s in stories if isinstance(s, dict)]


def _apply_window(stories: List[dict], window_hours: int, max_stories: int) -> List[dict]:
    now = time.time()
    cutoff = now - (window_hours * 3600)

    filtered: List[dict] = []
    dropped = 0

    for s in stories:
        ts = s.get("timestamp")
        if ts is None:
            dropped += 1
            continue
        try:
            tsf = float(ts)
        except Exception:
            dropped += 1
            continue
        if tsf >= cutoff:
            filtered.append(s)

    filtered.sort(key=lambda x: float(x.get("timestamp", 0)))
    if len(filtered) > max_stories:
        filtered = filtered[-max_stories:]

    return filtered


# ============================================================
# CLUSTER RANKING
# ============================================================

def _rank_clusters(clusters: List[dict]) -> List[dict]:
    usage_map = _get_narrative_usage_map()

    def score(cluster: dict) -> float:
        stories = cluster.get("stories", [])
        if not stories:
            return 0.0

        avg_importance = sum(float(s.get("importance", 0)) for s in stories) / max(1, len(stories))
        recency = max(float(s.get("timestamp", 0)) for s in stories)
        size = len(stories)

        base_score = (avg_importance * 2.0) + float(size) + (recency / 1e10)
        penalty = _cluster_reuse_penalty(cluster, usage_map)

        return base_score - penalty

    return sorted(clusters, key=score, reverse=True)


# ============================================================
# NUMERIC + SIGNAL SNAPSHOTS (NEW)
# ============================================================

def _try_chainstack_numeric() -> Optional[Dict[str, Any]]:
    """
    Returns numeric_context dict or None if unavailable.
    """
    try:
        from backend.script_engine.onchain.chainstack_numeric_enricher import generate_numeric_enrichment
        numeric = generate_numeric_enrichment()
        if isinstance(numeric, dict) and numeric:
            return numeric
    except Exception as e:
        print(f"[INTEL][WARN] Chainstack numeric enrichment failed: {e}")
    return None


def _try_signal_snapshot() -> Optional[Any]:
    """
    If you have a callable entrypoint in signal_engine, wire it here.
    Safe no-op if not available.
    """
    try:
        from backend.script_engine.signals import signal_engine
        # Prefer a function if present (do not guess names aggressively)
        fn = getattr(signal_engine, "run_signal_engine", None) or getattr(signal_engine, "generate_signals", None)
        if callable(fn):
            sig = fn()
            return sig
    except Exception as e:
        print(f"[INTEL][WARN] Signal snapshot failed: {e}")
    return None


# ============================================================
# MAIN RUN
# ============================================================

def run_intelligence(*, skip_ingest: bool = False) -> Dict[str, Any]:
    run_id = str(int(time.time()))
    run_dir = ARTIFACTS_DIR / run_id
    latest_dir = ARTIFACTS_DIR / "latest"

    _ensure_dir(run_dir)
    _ensure_dir(EPISODES_DIR)

    # Config
    window_hours = _env_int("TOKN_CLUSTER_WINDOW_HOURS", 36)
    max_stories = _env_int("TOKN_CLUSTER_MAX_STORIES", 800)
    max_clusters = _env_int("TOKN_MAX_CLUSTERS", 10)

    enable_chainstack_numeric = _env_bool("TOKN_ENABLE_CHAINSTACK_NUMERIC", True)
    enable_signal_snapshot = _env_bool("TOKN_ENABLE_SIGNAL_SNAPSHOT", False)

    meta: Dict[str, Any] = {
        "run_id": run_id,
        "ts": time.time(),
        "window_hours": window_hours,
        "max_stories": max_stories,
        "max_clusters": max_clusters,
        "features": {
            "chainstack_numeric": enable_chainstack_numeric,
            "signal_snapshot": enable_signal_snapshot,
            "reuse_penalty": True,
        },
    }

    # -------------------------------------------------
    # INGEST
    # -------------------------------------------------
    if not skip_ingest:
        from backend.rest.routes.ingest_v2.ingest_controller import run_ingestion
        run_ingestion()

    # -------------------------------------------------
    # LOAD + WINDOW
    # -------------------------------------------------
    stories = _load_story_lake()
    windowed = _apply_window(stories, window_hours, max_stories)
    _atomic_write_json(run_dir / "story_lake_window.json", windowed)
    meta["story_lake_total"] = len(stories)
    meta["windowed_count"] = len(windowed)

    # -------------------------------------------------
    # NUMERIC + SIGNAL SNAPSHOTS (episode-level)
    # -------------------------------------------------
    numeric_context = None
    if enable_chainstack_numeric:
        numeric_context = _try_chainstack_numeric()
        if numeric_context:
            _atomic_write_json(run_dir / "numeric_context.json", numeric_context)
            meta["numeric_context_keys"] = sorted(list(numeric_context.keys()))
        else:
            meta["numeric_context_keys"] = []

    signal_context = None
    if enable_signal_snapshot:
        signal_context = _try_signal_snapshot()
        if signal_context is not None:
            _atomic_write_json(run_dir / "signal_context.json", signal_context)
            meta["signal_context_ok"] = True
        else:
            meta["signal_context_ok"] = False

    # -------------------------------------------------
    # CLUSTER
    # -------------------------------------------------
    from backend.script_engine.editorial.run_semantic_clustering import run_semantic_clustering

    clusters = run_semantic_clustering(windowed)
    clusters = _rank_clusters(clusters)
    clusters = clusters[:max_clusters]

    _atomic_write_json(run_dir / "story_refined_clusters.json", clusters)
    _atomic_write_json(LEGACY_REFINED_CLUSTERS, clusters)
    meta["cluster_count"] = len(clusters)

    # -------------------------------------------------
    # NARRATIVE (existing script)
    # -------------------------------------------------
    narrative_script = str(BASE_DIR / "backend/script_engine/editorial/narrative_synthesizer.py")
    _run_subprocess([PYTHON, PYTHON_ARG, narrative_script])

    briefs = _safe_load_json(LEGACY_NARRATIVE_BRIEFS) if LEGACY_NARRATIVE_BRIEFS.exists() else []
    _atomic_write_json(run_dir / "narrative_briefs.json", briefs)
    meta["brief_count"] = len(briefs) if isinstance(briefs, list) else None

    # -------------------------------------------------
    # DIALOGUE (existing script)
    # -------------------------------------------------
    dialogue_script = str(BASE_DIR / "backend/script_engine/editorial/dialogue_generator.py")
    _run_subprocess([PYTHON, PYTHON_ARG, dialogue_script])

    dialogue = _safe_load_json(LEGACY_DIALOGUE_BLOCKS) if LEGACY_DIALOGUE_BLOCKS.exists() else []
    _atomic_write_json(run_dir / "dialogue_blocks.json", dialogue)
    meta["dialogue_block_count"] = len(dialogue) if isinstance(dialogue, list) else None

    # -------------------------------------------------
    # TIMELINE
    # -------------------------------------------------
    from backend.script_engine.editorial.timeline_builder_v6 import build_timeline

    timeline = build_timeline(dialogue)
    _atomic_write_json(run_dir / "timeline.json", timeline)

    # -------------------------------------------------
    # META + LATEST + PREVIEW
    # -------------------------------------------------
    _atomic_write_json(run_dir / "meta.json", meta)
    _symlink_latest(latest_dir, run_dir)

    preview_path = EPISODES_DIR / f"int_run_{run_id}_preview.json"
    _atomic_write_json(preview_path, timeline)

    return {
        "run_id": run_id,
        "clusters": len(clusters),
        "briefs": len(briefs) if isinstance(briefs, list) else 0,
        "dialogue_blocks": len(dialogue) if isinstance(dialogue, list) else 0,
        "timeline_blocks": len(timeline) if isinstance(timeline, list) else 0,
        "preview": str(preview_path),
    }


if __name__ == "__main__":
    skip = os.getenv("TOKN_SKIP_INGEST", "0").strip().lower() in ("1", "true", "yes")
    print(json.dumps(run_intelligence(skip_ingest=skip), indent=2))
