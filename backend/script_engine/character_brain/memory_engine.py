#!/usr/bin/env python3

"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS CHARACTER BRAIN
Memory Engine

Purpose
-------
Persistent narrative memory layer for ToknNews.

This module tracks:
• recent episode items
• persistent story threads
• entity memory
• domain heat
• anchor usage history
• callback candidates for future shows

Design Notes
------------
• JSON-backed persistence
• additive and broadcast-safe
• OpenClaw-friendly
• supports continuity across episodes
• supports future promo and TTS conditioning

Primary File
------------
/opt/toknnews/backend/script_engine/character_brain/character_memory.json

Author: TOKN Systems
"""

from __future__ import annotations

import json
import os
import time
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent
MEM_PATH = BASE_DIR / "character_memory.json"
TMP_MEM_PATH = BASE_DIR / "character_memory.tmp.json"


# ---------------------------------------------------------
# DEFAULT STATE
# ---------------------------------------------------------

DEFAULT_MEMORY: Dict[str, Any] = {
    "meta": {
        "version": 2,
        "updated_at": None,
        "created_at": None,
    },
    "recent_items": [],
    "story_threads": {},
    "entity_memory": {},
    "domain_heatmap": {},
    "anchor_memory": {},
    "episode_log": [],
}


# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def utc_now_iso() -> str:
    return utc_now().isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def parse_dt(value: Any) -> datetime | None:
    text = clean(value)
    if not text:
        return None

    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"

        dt = datetime.fromisoformat(text)

        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)

        return dt.astimezone(UTC)
    except Exception:
        return None


def atomic_write_json(path: Path, tmp_path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(payload, indent=2))
    tmp_path.replace(path)


def unique_preserve(items: List[Any]) -> List[Any]:
    seen = set()
    out: List[Any] = []

    for item in items:
        key = repr(item)
        if key in seen:
            continue
        seen.add(key)
        out.append(item)

    return out


def _fresh_memory() -> Dict[str, Any]:
    payload = deepcopy(DEFAULT_MEMORY)
    now = utc_now_iso()
    payload["meta"]["created_at"] = now
    payload["meta"]["updated_at"] = now
    return payload


# ---------------------------------------------------------
# LOAD / SAVE
# ---------------------------------------------------------

def load_memory() -> Dict[str, Any]:
    if not MEM_PATH.exists():
        return _fresh_memory()

    try:
        data = json.loads(MEM_PATH.read_text())
    except Exception:
        return _fresh_memory()

    if not isinstance(data, dict):
        return _fresh_memory()

    merged = deepcopy(DEFAULT_MEMORY)
    merged.update(data)

    merged["meta"] = safe_dict(merged.get("meta"))
    merged["recent_items"] = safe_list(merged.get("recent_items"))
    merged["story_threads"] = safe_dict(merged.get("story_threads"))
    merged["entity_memory"] = safe_dict(merged.get("entity_memory"))
    merged["domain_heatmap"] = safe_dict(merged.get("domain_heatmap"))
    merged["anchor_memory"] = safe_dict(merged.get("anchor_memory"))
    merged["episode_log"] = safe_list(merged.get("episode_log"))

    if not clean(merged["meta"].get("created_at")):
        merged["meta"]["created_at"] = utc_now_iso()

    if not clean(merged["meta"].get("updated_at")):
        merged["meta"]["updated_at"] = utc_now_iso()

    return merged


def save_memory(mem: Dict[str, Any]) -> None:
    payload = safe_dict(mem)
    payload.setdefault("meta", {})
    payload["meta"]["updated_at"] = utc_now_iso()

    if not clean(payload["meta"].get("created_at")):
        payload["meta"]["created_at"] = utc_now_iso()

    atomic_write_json(MEM_PATH, TMP_MEM_PATH, payload)


# ---------------------------------------------------------
# DECAY / CLEANUP
# ---------------------------------------------------------

def decay_recent_items(mem: Dict[str, Any], lookback_hours: int = 6) -> Dict[str, Any]:
    cutoff = utc_now() - timedelta(hours=lookback_hours)
    new_items: List[Dict[str, Any]] = []

    for item in safe_list(mem.get("recent_items")):
        row = safe_dict(item)
        dt = parse_dt(row.get("timestamp"))
        if dt is None or dt < cutoff:
            continue

        age_minutes = max(0.0, (utc_now() - dt).total_seconds() / 60.0)
        decay_factor = max(0.15, 1.0 - (age_minutes / float(lookback_hours * 60)))
        row["weight"] = round(safe_float(row.get("weight"), 1.0) * decay_factor, 4)
        new_items.append(row)

    mem["recent_items"] = new_items[-250:]
    return mem


def decay_domain_heat(mem: Dict[str, Any], decay_hours: int = 8) -> Dict[str, Any]:
    heatmap = safe_dict(mem.get("domain_heatmap"))
    now = utc_now()

    for domain, payload in heatmap.items():
        info = safe_dict(payload)
        updated = parse_dt(info.get("updated"))
        if updated is None:
            continue

        age_minutes = max(0.0, (now - updated).total_seconds() / 60.0)
        decay_factor = max(0.05, 1.0 - (age_minutes / float(decay_hours * 60)))
        info["score"] = round(safe_float(info.get("score"), 0.0) * decay_factor, 4)
        info["updated"] = now.isoformat()
        heatmap[domain] = info

    mem["domain_heatmap"] = heatmap
    return mem


def prune_story_threads(mem: Dict[str, Any], max_age_days: int = 14) -> Dict[str, Any]:
    cutoff = utc_now() - timedelta(days=max_age_days)
    threads = safe_dict(mem.get("story_threads"))
    kept: Dict[str, Any] = {}

    for thread_id, payload in threads.items():
        row = safe_dict(payload)
        last_seen = parse_dt(row.get("last_seen"))
        if last_seen is None or last_seen < cutoff:
            continue
        kept[thread_id] = row

    mem["story_threads"] = kept
    return mem


def prune_episode_log(mem: Dict[str, Any], keep_last: int = 100) -> Dict[str, Any]:
    mem["episode_log"] = safe_list(mem.get("episode_log"))[-keep_last:]
    return mem


# ---------------------------------------------------------
# UPDATE HELPERS
# ---------------------------------------------------------

def update_domain_heat(mem: Dict[str, Any], domain: str, bump: float = 1.0) -> Dict[str, Any]:
    domain = clean(domain).lower() or "general"
    heat = safe_dict(mem.get("domain_heatmap"))
    now = utc_now_iso()

    payload = safe_dict(heat.get(domain))
    payload["score"] = round(safe_float(payload.get("score"), 0.0) + bump, 4)
    payload["updated"] = now

    heat[domain] = payload
    mem["domain_heatmap"] = heat
    return mem


def update_story_thread(
    mem: Dict[str, Any],
    thread_id: str,
    headline: str = "",
    domain: str = "",
    entity: str = "",
    summary: str = "",
    anchors: List[str] | None = None,
) -> Dict[str, Any]:
    thread_id = clean(thread_id)
    if not thread_id:
        return mem

    threads = safe_dict(mem.get("story_threads"))
    payload = safe_dict(threads.get(thread_id))
    now = utc_now_iso()

    payload["thread_id"] = thread_id
    payload["headline"] = clean(headline) or clean(payload.get("headline"))
    payload["domain"] = clean(domain).lower() or clean(payload.get("domain")) or "general"
    payload["entity"] = clean(entity) or clean(payload.get("entity"))
    payload["last_summary"] = clean(summary) or clean(payload.get("last_summary"))
    payload["mentions"] = safe_int(payload.get("mentions"), 0) + 1
    payload["last_seen"] = now

    if not clean(payload.get("first_seen")):
        payload["first_seen"] = now

    existing_anchors = safe_list(payload.get("anchors_used"))
    payload["anchors_used"] = unique_preserve(existing_anchors + safe_list(anchors or []))[:10]

    threads[thread_id] = payload
    mem["story_threads"] = threads
    return mem


def update_entity_memory(
    mem: Dict[str, Any],
    entity: str,
    domain: str = "",
    signal_type: str = "",
    summary: str = "",
) -> Dict[str, Any]:
    entity = clean(entity).upper()
    if not entity:
        return mem

    entities = safe_dict(mem.get("entity_memory"))
    payload = safe_dict(entities.get(entity))
    now = utc_now_iso()

    payload["entity"] = entity
    payload["domain"] = clean(domain).lower() or clean(payload.get("domain")) or "general"
    payload["last_signal_type"] = clean(signal_type) or clean(payload.get("last_signal_type"))
    payload["last_summary"] = clean(summary) or clean(payload.get("last_summary"))
    payload["mentions"] = safe_int(payload.get("mentions"), 0) + 1
    payload["last_seen"] = now

    if not clean(payload.get("first_seen")):
        payload["first_seen"] = now

    entities[entity] = payload
    mem["entity_memory"] = entities
    return mem


def update_anchor_memory(
    mem: Dict[str, Any],
    anchors: List[str] | None,
    domain: str = "",
    thread_id: str = "",
) -> Dict[str, Any]:
    anchor_memory = safe_dict(mem.get("anchor_memory"))
    now = utc_now_iso()
    domain = clean(domain).lower() or "general"

    for anchor in safe_list(anchors or []):
        name = clean(anchor).lower()
        if not name:
            continue

        payload = safe_dict(anchor_memory.get(name))
        payload["anchor"] = name
        payload["last_seen"] = now
        payload["appearances"] = safe_int(payload.get("appearances"), 0) + 1

        domains = safe_dict(payload.get("domains"))
        domains[domain] = safe_int(domains.get(domain), 0) + 1
        payload["domains"] = domains

        threads = safe_list(payload.get("threads"))
        if clean(thread_id):
            threads = unique_preserve(threads + [thread_id])[-25:]
        payload["threads"] = threads

        anchor_memory[name] = payload

    mem["anchor_memory"] = anchor_memory
    return mem


def add_recent_item(
    mem: Dict[str, Any],
    headline: str,
    domain: str,
    summary: str = "",
    thread_id: str = "",
    entity: str = "",
    weight: float = 1.0,
) -> Dict[str, Any]:
    items = safe_list(mem.get("recent_items"))
    items.append(
        {
            "headline": clean(headline),
            "domain": clean(domain).lower() or "general",
            "summary": clean(summary),
            "thread_id": clean(thread_id),
            "entity": clean(entity).upper(),
            "timestamp": utc_now_iso(),
            "weight": round(max(0.1, safe_float(weight, 1.0)), 4),
        }
    )
    mem["recent_items"] = items[-250:]
    return mem


# ---------------------------------------------------------
# PUBLIC ENTRYPOINTS
# ---------------------------------------------------------

def update_memory_with_story(enriched: Dict[str, Any]) -> Dict[str, Any]:
    row = safe_dict(enriched)
    mem = load_memory()

    headline = clean(row.get("headline") or row.get("title"))
    domain = clean(row.get("domain")) or "general"
    summary = clean(row.get("summary"))
    entity = clean(row.get("entity"))
    signal_type = clean(row.get("signal_type"))
    thread_id = clean(row.get("thread_id"))
    anchors = safe_list(row.get("anchors"))

    if not thread_id:
        parts = [
            domain.lower() or "general",
            entity.upper() or "NONE",
            signal_type.lower() or "signal",
        ]
        thread_id = "::".join(parts)

    mem = add_recent_item(
        mem=mem,
        headline=headline,
        domain=domain,
        summary=summary,
        thread_id=thread_id,
        entity=entity,
        weight=1.0,
    )
    mem = update_story_thread(
        mem=mem,
        thread_id=thread_id,
        headline=headline,
        domain=domain,
        entity=entity,
        summary=summary,
        anchors=anchors,
    )
    mem = update_entity_memory(
        mem=mem,
        entity=entity,
        domain=domain,
        signal_type=signal_type,
        summary=summary,
    )
    mem = update_anchor_memory(
        mem=mem,
        anchors=anchors,
        domain=domain,
        thread_id=thread_id,
    )
    mem = update_domain_heat(
        mem=mem,
        domain=domain,
        bump=1.0,
    )

    mem = decay_recent_items(mem)
    mem = decay_domain_heat(mem)
    mem = prune_story_threads(mem)
    mem = prune_episode_log(mem)

    save_memory(mem)
    return mem


def update_memory_with_episode(episode_payload: Dict[str, Any]) -> Dict[str, Any]:
    row = safe_dict(episode_payload)
    mem = load_memory()

    episode_id = clean(row.get("episode_id")) or f"episode_{int(time.time())}"
    domains = safe_list(row.get("domains"))
    anchors = safe_list(row.get("anchors"))
    thesis = clean(row.get("episode_thesis"))
    callback_threads = safe_list(row.get("callback_threads"))

    mem.setdefault("episode_log", [])
    mem["episode_log"].append(
        {
            "episode_id": episode_id,
            "timestamp": utc_now_iso(),
            "episode_thesis": thesis,
            "domains": domains[:10],
            "anchors": anchors[:10],
            "callback_threads": callback_threads[:10],
        }
    )

    for domain in domains:
        mem = update_domain_heat(mem, domain, bump=0.6)

    mem = update_anchor_memory(mem, anchors=anchors, domain=clean(domains[0]) if domains else "general")

    mem = decay_recent_items(mem)
    mem = decay_domain_heat(mem)
    mem = prune_story_threads(mem)
    mem = prune_episode_log(mem)

    save_memory(mem)
    return mem


def get_callback_candidates(limit: int = 10) -> List[Dict[str, Any]]:
    mem = load_memory()
    threads = safe_dict(mem.get("story_threads"))

    rows = sorted(
        [safe_dict(v) for v in threads.values()],
        key=lambda x: (
            safe_int(x.get("mentions"), 0),
            clean(x.get("last_seen")),
        ),
        reverse=True,
    )

    return rows[:max(1, limit)]


def get_domain_heatmap() -> Dict[str, Any]:
    mem = load_memory()
    return safe_dict(mem.get("domain_heatmap"))


def get_anchor_history(anchor: str) -> Dict[str, Any]:
    mem = load_memory()
    return safe_dict(safe_dict(mem.get("anchor_memory")).get(clean(anchor).lower()))


if __name__ == "__main__":
    print(json.dumps(load_memory(), indent=2))
