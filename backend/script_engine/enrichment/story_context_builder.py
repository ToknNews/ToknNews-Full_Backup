#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝

TOKNNEWS ENRICHMENT ENGINE
Story Context Builder

Purpose
-------
Builds anchor-ready context packets combining all upstream layers.

Inputs
------
show_structure.json
show_director.json
entity_resolution_map.json
article_enrichment.json

Output
------
story_context_packets.json

Author: TOKN Systems
"""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List

# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

STRUCTURE_PATH = Path("/opt/toknnews/data/show_structure.json")
DIRECTOR_PATH = Path("/opt/toknnews/data/show_director.json")
ENTITY_PATH = Path("/opt/toknnews/data/entity_resolution_map.json")
ARTICLE_PATH = Path("/opt/toknnews/data/article_enrichment.json")

OUTPUT_PATH = Path("/opt/toknnews/data/story_context_packets.json")
TMP_PATH = OUTPUT_PATH.with_suffix(".tmp")

# ---------------------------------------------------------
# HELPERS
# ---------------------------------------------------------

def clean(v: Any) -> str:
    return "" if v is None else str(v).strip()

def safe_list(v: Any) -> List[Any]:
    return v if isinstance(v, list) else []

def safe_dict(v: Any) -> Dict[str, Any]:
    return v if isinstance(v, dict) else {}

def now_ts():
    return time.time()

def atomic_write(path: Path, tmp: Path, payload: Any):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_text(json.dumps(payload, indent=2))
    tmp.replace(path)

# ---------------------------------------------------------
# LOOKUPS
# ---------------------------------------------------------

def build_article_lookup(data: Dict[str, Any]) -> Dict[str, Dict]:
    return {clean(a["url"]): a for a in data.get("articles", [])}

def build_entity_lookup(data: Dict[str, Any]) -> Dict[str, Dict]:
    return data.get("entities", {})

# ---------------------------------------------------------
# CORE LOGIC
# ---------------------------------------------------------

def build_packet(story, act, entity_map, article_map):

    entity = clean(story.get("entity"))
    url = clean(story.get("raw_url"))

    entity_data = entity_map.get(entity, {})
    article_data = article_map.get(url, {})

    resolved_entity = entity_data.get("display_label", entity)

    article_summary = clean(article_data.get("summary"))
    key_takeaway = clean(article_data.get("key_takeaway"))

    base_summary = clean(story.get("summary"))

    # fallback safety
    if not article_summary:
        article_summary = base_summary

    domain = clean(act.get("domain"))
    signal_type = clean(story.get("signal_type"))

    # ---------------------------------------------------------
    # 🔥 SIGNAL INTELLIGENCE (NEW)
    # ---------------------------------------------------------

    # WHAT IS HAPPENING
    signal_frame = f"{resolved_entity} shows activity through {signal_type}"

    # WHY IT MATTERS (REAL UPGRADE)
    if domain == "macro":
        why = f"{resolved_entity} reflects macro pressure and broader market positioning"
        risk = f"If macro conditions tighten further, {resolved_entity} may struggle to maintain momentum"

    elif domain == "crypto_major":
        why = f"Large flows in {resolved_entity} indicate positioning shifts among major players"
        risk = f"If flows reverse, it could signal weakening conviction"

    elif domain == "defi":
        why = f"{resolved_entity} activity reflects underlying protocol strength and real usage"
        risk = f"If usage drops, it suggests narrative may be ahead of fundamentals"

    elif domain == "news":
        why = f"This headline shapes sentiment around {resolved_entity} but may not reflect structural change"
        risk = f"If sentiment diverges from reality, traders may misprice the situation"

    elif domain == "crypto_alt":
        why = f"{resolved_entity} represents speculative rotation and emerging risk appetite"
        risk = f"If momentum fades, these moves tend to unwind quickly"

    elif domain == "meme":
        why = f"{resolved_entity} reflects pure speculative behavior and short-term attention"
        risk = f"These moves are highly unstable and prone to rapid reversal"

    else:
        why = f"{resolved_entity} contributes to current market dynamics"
        risk = f"Unclear durability in this signal"

    # DEBATE ANGLE (UPGRADED)
    debate = (
        f"Is this a durable signal around {resolved_entity}, "
        f"or just short-term positioning reacting to noise?"
    )

    # ---------------------------------------------------------
    # ANCHOR ROLES (FIXED)
    # ---------------------------------------------------------

    roles = safe_dict(story.get("anchor_roles"))

    if not roles or not roles.get("lead"):
        # fallback mapping
        if domain == "macro":
            roles = {"lead": "bond", "counter": "cash"}
        elif domain == "defi":
            roles = {"lead": "reef", "counter": "ledger"}
        elif domain == "news":
            roles = {"lead": "ivy", "counter": "bond"}
        elif domain == "crypto_major":
            roles = {"lead": "ledger", "counter": "bond"}
        elif domain == "crypto_alt":
            roles = {"lead": "cash", "counter": "lawson"}
        elif domain == "meme":
            roles = {"lead": "cash", "counter": "lawson"}
        else:
            roles = {"lead": "bond", "counter": "cash"}

    roles["support"] = "chip"

    # ---------------------------------------------------------
    # FINAL PACKET
    # ---------------------------------------------------------

    return {
        "title": clean(story.get("title")),
        "entity": entity,
        "resolved_entity": resolved_entity,
        "domain": domain,
        "signal_type": signal_type,

        "summary": base_summary,
        "article_summary": article_summary,
        "key_takeaway": key_takeaway,

        "signal_frame": signal_frame,
        "why_it_matters": why,
        "risk_frame": risk,
        "debate_angle": debate,

        "anchor_roles": roles,
        "raw_url": url
    }

# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def main():
    if not STRUCTURE_PATH.exists():
        raise FileNotFoundError("Missing show_structure.json")

    structure = json.loads(STRUCTURE_PATH.read_text())
    director = json.loads(DIRECTOR_PATH.read_text())
    entity_map = build_entity_lookup(json.loads(ENTITY_PATH.read_text()))
    article_map = build_article_lookup(json.loads(ARTICLE_PATH.read_text()))

    packets = []

    for act in structure.get("acts", []):
        for story in act.get("stories", []):
            packets.append(
                build_packet(story, act, entity_map, article_map)
            )

    payload = {
        "generated_at": now_ts(),
        "count": len(packets),
        "stories": packets
    }

    atomic_write(OUTPUT_PATH, TMP_PATH, payload)

    print(f"[CONTEXT BUILDER] stories={len(packets)}")

if __name__ == "__main__":
    main()
