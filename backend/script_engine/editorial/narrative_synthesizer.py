#!/usr/bin/env python3
"""
narrative_synthesizer.py
ToknNews — Narrative Brief Generator (v8 numeric-hook enabled)

Adds:
- Pulls latest Chainstack numeric_context (if present)
- Injects a compact numeric hook into pd_hints for downstream dialogue realism
- Keeps no-invent/no-speculate rules
"""

import json
import time
import os
import random
import openai
from uuid import uuid4
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, Any, List, Optional

load_dotenv("/opt/toknnews/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

CLUSTER_PATH = Path("/opt/toknnews/data/stories/story_refined_clusters.json")
OUT_PATH     = Path("/opt/toknnews/data/stories/narrative_briefs.json")
ART_LATEST   = Path("/opt/toknnews/data/artifacts/latest")

ONCHAIN_MIN_USD = 5_000_000
DUAL_ANCHOR_HEAT_THRESHOLD = float(os.getenv("TOKN_DUAL_ANCHOR_HEAT", "6.0"))

DOMAIN_LEAD_ANCHOR = {
    "markets": "cash",
    "macro": "bond",
    "defi": "reef",
    "onchain": "reef",
    "regulation": "lawson",
    "sentiment": "ivy",
    "culture": "penny",
    "ai": "ledger",
    "general": "bond"
}

DOMAIN_SECONDARY_ANCHOR = {
    "markets": "bond",
    "macro": "cash",
    "defi": "ledger",
    "onchain": "ledger",
    "regulation": "bond",
    "sentiment": "chip",
    "culture": "chip",
    "ai": "neura",
    "general": "chip",
}

ANGLE_MODES = [
    "Positioning lens (flows vs price)",
    "Risk-transfer lens (who absorbs risk)",
    "Incentive lens (who benefits / who is trapped)",
    "Second-order lens (what breaks next)",
    "Liquidity-rotation lens (capital moving internally vs entering/exiting)",
]

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default

def _cluster_heat(stories: List[Dict[str, Any]]) -> float:
    if not stories:
        return 5.0
    vals = []
    for s in stories:
        imp = s.get("importance")
        if imp is None:
            imp = (s.get("signals") or {}).get("composite_heat")
        vals.append(_safe_float(imp, 5.0))
    avg = sum(vals) / max(1, len(vals))
    return max(0.0, min(10.0, avg))

def _cluster_ts(stories: List[Dict[str, Any]]) -> float:
    if not stories:
        return time.time()
    return max(_safe_float(s.get("timestamp"), 0.0) for s in stories) or time.time()

def _load_latest_numeric_context() -> Optional[Dict[str, Any]]:
    path = ART_LATEST / "numeric_context.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return data if isinstance(data, dict) else None
    except Exception:
        return None

def _build_numeric_hook(numeric: Optional[Dict[str, Any]], domain: str) -> str:
    """
    Compact, spoken-ready hook. No speculation. Use only available fields.
    """
    if not numeric or not isinstance(numeric, dict):
        return ""

    chains = numeric.get("chains") or {}
    eth = chains.get("ethereum") or {}
    base = chains.get("base") or {}
    arb = chains.get("arbitrum") or {}

    lines = []

    # ETH price (DEX) if present
    eth_price = ((eth.get("price") or {}).get("usd"))
    if eth_price:
        lines.append(f"ETH around ${eth_price:,.0f} (DEX-derived snapshot).")

    # L2 activity signals if present
    def _tx_line(label: str, obj: dict):
        act = obj.get("activity") or {}
        tx5 = act.get("tx_count_5m")
        trend = act.get("tx_trend")
        if isinstance(tx5, (int, float)) and trend:
            return f"{label} about {int(tx5):,} tx in 5 minutes, trend {trend}."
        return ""

    for lab, obj in (("Ethereum", eth), ("Base", base), ("Arbitrum", arb)):
        ln = _tx_line(lab, obj)
        if ln:
            lines.append(ln)

    # Keep hook short
    if not lines:
        return ""

    # Domain tailoring (light)
    if domain in ("onchain", "defi"):
        return "Numeric hook: " + " ".join(lines[:2])
    if domain in ("markets", "macro"):
        return "Numeric hook: " + " ".join(lines[:2])
    return "Numeric hook: " + " ".join(lines[:1])

def should_process_cluster(cluster):
    stories = cluster.get("stories", [])
    if not stories:
        return False
    if len(stories) >= 2:
        return True
    for s in stories:
        if s.get("source") == "moralis_stream":
            if s.get("value_usd", 0) >= ONCHAIN_MIN_USD or s.get("tx_hash"):
                return True
    for s in stories:
        if s.get("source") == "onchain_synth_v1" and s.get("raw_onchain_count", 0) >= 1:
            return True
    return False

def should_process_as_context(cluster):
    stories = cluster.get("stories", [])
    if not stories:
        return False
    domain = stories[0].get("domain", "")
    if domain not in ("markets", "onchain", "defi"):
        return False
    for s in stories:
        if s.get("market_context"):
            return True
        if s.get("event_type") == "asset_trend":
            return True
    return True

def select_anchors(domain: str, *, heat: float, tier: str) -> list:
    primary = DOMAIN_LEAD_ANCHOR.get(domain, "bond")
    secondary = DOMAIN_SECONDARY_ANCHOR.get(domain)
    if (tier == "lead" or heat >= DUAL_ANCHOR_HEAT_THRESHOLD) and secondary and secondary != primary:
        return [primary, secondary]
    return [primary]

def build_prompt(stories, domain, tier, angle_mode: str, heat: float, numeric_hook: str):
    headlines = "\n".join(f"- {s.get('headline','')}" for s in stories)

    return f"""
You are the editorial intelligence layer of ToknNews.

TIER: {tier.upper()}
DOMAIN: {domain}
ANGLE MODE: {angle_mode}
HEAT: {heat:.1f} / 10

STORIES (headlines only):
{headlines}

NUMERIC SNAPSHOT (use only if relevant; do not invent):
{numeric_hook}

HARD RULES:
- Do NOT invent facts or numbers
- Do NOT speculate or predict
- Natural spoken English (broadcast-ready)
- Prefer mechanisms and incentives over adjectives

OUTPUT QUALITY RULES:
- Thesis must include BOTH:
  (1) a directional claim, AND
  (2) a vulnerability/counter-risk that could invalidate the claim
- "What people are missing" must be concrete (mechanism/incentive/second-order)
- If numeric snapshot is present, incorporate at least ONE numeric reference (only if it fits the story)

Return JSON ONLY:
{{
  "thesis": "...",
  "what_happened": "...",
  "why_it_matters": "...",
  "what_people_are_missing": "...",
  "recommended_runtime_sec": {30 if tier == "context" else 45}
}}
""".strip()

def main():
    clusters = json.loads(CLUSTER_PATH.read_text())
    output = []

    numeric = _load_latest_numeric_context()

    for cluster in clusters:
        stories = cluster.get("stories", [])
        if not stories:
            continue

        domain = stories[0].get("domain", "general")

        if should_process_cluster(cluster):
            tier = "lead"
        elif should_process_as_context(cluster):
            tier = "context"
        else:
            continue

        heat = _cluster_heat(stories)
        angle_mode = random.choice(ANGLE_MODES)
        numeric_hook = _build_numeric_hook(numeric, domain)

        prompt = build_prompt(stories, domain, tier, angle_mode, heat, numeric_hook)

        try:
            rsp = openai.ChatCompletion.create(
                model=os.getenv("TOKN_NARRATIVE_MODEL", "gpt-4.1"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.25,
                max_tokens=600,
                request_timeout=30
            )

            data = json.loads(rsp.choices[0].message.content)

            output.append({
                "narrative_id": str(uuid4()),
                "tier": tier,
                "domain": domain,
                "heat": heat,
                "angle_mode": angle_mode,
                "anchors": select_anchors(domain, heat=heat, tier=tier),
                "thesis": data["thesis"],
                "context": {
                    "what_happened": data["what_happened"],
                    "why_it_matters": data["why_it_matters"],
                    "what_people_are_missing": data["what_people_are_missing"]
                },
                "recommended_runtime_sec": data.get("recommended_runtime_sec", 45),
                "source_count": len(stories),
                "ts": _cluster_ts(stories),
                "pd_hints": {
                    # downstream prompt can use this safely
                    "numeric_hook": numeric_hook
                } if numeric_hook else {},
            })

        except Exception as e:
            print("[NARRATIVE ERROR]", e)

    OUT_PATH.write_text(json.dumps(output, indent=2))
    print(f"[NARRATIVE] Generated {len(output)} narrative briefs → {OUT_PATH}")

if __name__ == "__main__":
    main()
