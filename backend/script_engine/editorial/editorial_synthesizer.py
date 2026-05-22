#!/usr/bin/env python3
"""
editorial_synthesizer.py
ToknNews — Editorial Synthesis Layer

Upgrades:
- deterministic framing selection
- story normalization / validation
- ToknClaw trend-memory integration
- signal pressure scoring
- signal-aware heat boosts
- domain diversity guardrails
- 6-segment target framing
- culture / sentiment / memecoin preservation
- semantic trending detection hardening
- thread IDs for narrative continuity
- runtime estimation
- structured logs
"""

from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, DefaultDict
from collections import defaultdict
from pathlib import Path

import time
import json
import argparse
import uuid
import os
import random
import hashlib

# ============================================================
# OPTIONAL GROK CONTEXT INJECTION (SAFE, GATED)
# ============================================================

ENABLE_GROK_CONTEXT = os.getenv("ENABLE_GROK_CONTEXT", "false").lower() == "true"

if ENABLE_GROK_CONTEXT:
    try:
        from backend.script_engine.editorial.grok_context_injector import (
            generate_context_for_clusters
        )
    except Exception as e:
        print(f"[ESL][WARN] Grok context unavailable: {e}")
        ENABLE_GROK_CONTEXT = False

# ============================================================
# ANCHOR CANON
# ============================================================

DOMAIN_ANCHOR_PLAN = {
    "markets":    {"primary": "cash",   "secondary": "bond"},
    "macro":      {"primary": "bond",   "secondary": "chip"},
    "regulation": {"primary": "lawson", "secondary": "bond"},
    "onchain":    {"primary": "ledger", "secondary": "reef"},
    "defi":       {"primary": "reef",   "secondary": "ledger"},
    "ai":         {"primary": "neura",  "secondary": "chip"},
    "culture":    {"primary": "bitsy",  "secondary": "chip"},
    "general":    {"primary": "chip",   "secondary": None},
}

TARGET_EPISODE_RUNTIME = 600
MIN_EPISODE_RUNTIME = 520
MAX_SEGMENTS_PER_DOMAIN = 2
MAX_TOTAL_SEGMENTS = 6

# ============================================================
# FRAMING DIVERSIFICATION
# ============================================================

MARKETS_THESIS_TEMPLATES = [
    "Capital rotation is accelerating faster than price suggests, but that rotation is structurally fragile.",
    "Momentum is widening beyond majors, yet the stability of that move depends on flows that can reverse quickly.",
    "Market leadership looks stable on the surface, but positioning underneath is becoming more sensitive to shocks.",
    "Retail attention is expanding into smaller tokens, but that expansion can collapse if liquidity thins."
]

MARKETS_IMPL_TEMPLATES = [
    "If flows don’t confirm the move, the reversal tends to be sharper than the rally.",
    "When leadership broadens without durable support, volatility often rises before direction becomes obvious.",
    "The risk is not the move itself — it’s the speed of rotation when sentiment flips."
]

MACRO_THESIS_TEMPLATES = [
    "Policy signals appear stabilizing, but credit conditions remain uneven beneath the surface.",
    "Regulatory confidence is rising, yet that confidence can mask fragility if funding conditions tighten.",
    "Macro indicators look resilient, but internal liquidity distribution suggests stress points remain."
]

MACRO_IMPL_TEMPLATES = [
    "Markets often price the policy path early — then reprice violently when the data disagrees.",
    "The risk is a mismatch: policy confidence on top, tightening conditions underneath.",
    "If credit tightens faster than policy adapts, the real constraint shows up in flows, not headlines."
]

TREND_THESIS_TEMPLATES = [
    "Speculative attention is rotating into trending tokens, but sustainability depends on fragile participation.",
    "Trending tokens reflect expanding retail appetite, yet structural support often lags the narrative."
]

TREND_IMPL_TEMPLATES = [
    "These moves can persist longer than expected, but they tend to unwind fast when attention breaks.",
    "The signal is not the token — it’s the crowd behavior and how quickly it can reverse."
]

CONTEXT_THESIS_TEMPLATES = [
    "Stepping back, price action is less informative than positioning and risk transfer underneath.",
    "Stepping back, the surface calm can hide internal rotation that changes regime quickly."
]

CONTEXT_IMPL_TEMPLATES = [
    "These setups reward patience — and punish overconfidence when liquidity becomes one-sided.",
    "The key is not guessing direction; it’s recognizing where fragility is building."
]

CULTURE_THESIS_TEMPLATES = [
    "Retail narrative energy is building beneath the institutional surface, and that sentiment can move faster than fundamentals.",
    "Social attention is rotating into louder corners of the market, but that enthusiasm is highly unstable."
]

CULTURE_IMPL_TEMPLATES = [
    "When meme energy leads, price can detach from structure before snapping back.",
    "The crowd signal matters, but it usually matters most when it starts spilling into broader positioning."
]

# ============================================================
# SEGMENT SCHEMA
# ============================================================

@dataclass
class Segment:
    segment_id: str
    segment_type: str
    domain: str
    thesis: str
    facts: List[str]
    implication: str
    heat: float
    source_count: int
    ts: float
    anchor_plan: Dict[str, Any]
    pd_hints: Dict[str, Any]

    def to_dict(self):
        return asdict(self)

# ============================================================
# HELPERS
# ============================================================

def _now():
    return time.time()


def _clamp(v, lo=0.0, hi=10.0):
    return max(lo, min(hi, v))


def _normalize_story(s: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(s, dict):
        return {}
    out = dict(s)
    out["headline"] = str(out.get("headline") or "")
    out["summary"] = str(out.get("summary") or "")
    out["domain"] = str(out.get("domain") or "general").lower()
    out["importance"] = float(out.get("importance", 0) or 0)
    out["semantic_keys"] = out.get("semantic_keys") or {}
    out["toknclaw_context"] = out.get("toknclaw_context") or {}
    return out


def _heat(s):
    base = float(s.get("signals", {}).get("composite_heat", s.get("importance", 0)))
    return _clamp(base)


def _anchor_plan(domain: str):
    return DOMAIN_ANCHOR_PLAN.get(domain, DOMAIN_ANCHOR_PLAN["general"])


def _seed_from_facts(facts: List[str], fallback: str) -> str:
    blob = " | ".join(facts) if facts else fallback
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:16]


def _pick_template(templates: List[str], seed_key: str) -> str:
    if not templates:
        return ""
    r = random.Random(seed_key)
    return templates[r.randrange(0, len(templates))]


def _apply_pd_fields(seg: Dict[str, Any]) -> Dict[str, Any]:
    plan = seg.get("anchor_plan", {})
    primary = plan.get("primary", "chip")
    secondary = plan.get("secondary")
    tertiary = plan.get("tertiary")

    seg["persona_primary"] = primary
    seg["persona_secondary"] = secondary
    seg["persona_tertiary"] = tertiary
    seg["anchors"] = [a for a in (primary, secondary, tertiary) if a]
    return seg


def _gen_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _is_trending(s):
    semantic = s.get("semantic_keys", {}) or {}
    if semantic.get("event_type") == "asset_trend":
        return True

    headline = s.get("headline") or ""
    summary = s.get("summary") or ""
    t = f"{headline} {summary}".lower()
    return "coingecko" in t and "trending" in t


def _estimate_runtime(segments: List[Segment]) -> int:
    return int(sum(s.pd_hints.get("max_runtime_sec", 30) for s in segments))


def _story_assets(s: Dict[str, Any]) -> List[str]:
    semantic = s.get("semantic_keys", {}) or {}
    assets = semantic.get("assets") or []
    return [str(a).upper() for a in assets if a]


def _thread_id_for_stories(domain: str, stories: List[Dict[str, Any]]) -> str:
    assets: List[str] = []
    event_types: List[str] = []

    for s in stories[:5]:
        for a in _story_assets(s):
            if a not in assets:
                assets.append(a)
        evt = (s.get("semantic_keys", {}) or {}).get("event_type")
        if evt and evt not in event_types:
            event_types.append(evt)

    asset_part = assets[0] if assets else domain.upper()
    event_part = event_types[0] if event_types else "flow"
    return f"{asset_part}_{event_part}"


def _choose_angle(domain: str, stories: List[Dict[str, Any]]) -> str:
    text_blob = " ".join(
        f"{s.get('headline', '')} {s.get('summary', '')}".lower()
        for s in stories[:5]
    )

    if any(k in text_blob for k in ["liquidation", "forced", "cascade"]):
        return "Risk-transfer lens (who absorbs risk)"
    if any(k in text_blob for k in ["whale", "transfer", "exchange inflow", "exchange outflow"]):
        return "Positioning lens (flows vs price)"
    if any(k in text_blob for k in ["proposal", "governance", "regulation", "court", "sec"]):
        return "Incentive lens (who benefits / who is trapped)"
    if any(k in text_blob for k in ["rotation", "rebalancing", "leadership", "breadth"]):
        return "Liquidity-rotation lens (capital moving internally vs entering/exiting)"
    if domain == "culture":
        return "Second-order lens (what breaks next)"
    return "Positioning lens (flows vs price)"


def _numeric_phrase(numeric_context: Dict[str, Any]) -> str:
    if not isinstance(numeric_context, dict):
        return ""
    chains = numeric_context.get("chains", {}) or {}
    eth = chains.get("ethereum", {}) or {}
    activity = eth.get("activity", {}) or {}
    tx_trend = activity.get("tx_trend")
    if tx_trend == "up":
        return "Ethereum activity is also picking up in the background."
    return ""


def _signal_phrase(signal_context: List[Dict[str, Any]]) -> str:
    if not isinstance(signal_context, list):
        return ""
    for sig in signal_context:
        if not isinstance(sig, dict):
            continue
        if sig.get("confidence", 0) < 0.7:
            continue
        stype = sig.get("signal_type")
        if stype == "distribution":
            return "Positioning suggests supply may be building ahead of the move."
        if stype == "accumulation":
            return "Positioning suggests capital is building before price fully reflects it."
        if stype in {"capital_rotation", "liquidity_migration"}:
            return "Flows suggest capital is rotating internally rather than committing cleanly."
    return ""


def _extract_toknclaw_memory(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    for s in stories:
        ctx = s.get("toknclaw_context", {}) or {}
        memory = ctx.get("memory")
        if isinstance(memory, dict) and memory:
            return memory
    return {}


def _extract_toknclaw_deltas(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    for s in stories:
        ctx = s.get("toknclaw_context", {}) or {}
        deltas = ctx.get("deltas")
        if isinstance(deltas, dict) and deltas:
            return deltas
    return {}


def _signal_pressure(stories: List[Dict[str, Any]]) -> Dict[str, Any]:
    pressure = {
        "exchange_inflow": 0,
        "exchange_outflow": 0,
        "whale_transfer": 0,
        "defi_liquidation": 0
    }

    for s in stories:
        if s.get("source") != "toknclaw":
            continue
        sig = (s.get("signal_data", {}) or {}).get("signal_type") or (s.get("semantic_keys", {}) or {}).get("event_type")
        if sig in pressure:
            pressure[sig] += 1

    score = (
        pressure["exchange_inflow"] * 1.2 +
        pressure["exchange_outflow"] * 0.8 +
        pressure["whale_transfer"] * 1.0 +
        pressure["defi_liquidation"] * 1.5
    )

    return {
        "counts": pressure,
        "score": round(score, 2)
    }


def _build_domain_index(stories: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    by_domain: DefaultDict[str, List[Dict[str, Any]]] = defaultdict(list)
    for s in stories:
        by_domain[s.get("domain", "general")].append(s)
    return dict(by_domain)

# ============================================================
# ANCHOR MEMORY
# ============================================================

ANCHOR_MEMORY_DIR = Path("/opt/toknnews/data/anchors")

def load_anchor_memory(anchor: str) -> Dict[str, Any]:
    path = ANCHOR_MEMORY_DIR / f"{anchor}.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}

# ============================================================
# SYNTHESIS FUNCTIONS
# ============================================================

def synthesize_macro_segment(
    stories,
    *,
    numeric_context: Dict[str, Any] | None = None,
    signal_context: List[Dict[str, Any]] | None = None
):
    facts = [
        f for f in (
            (s.get("summary") or s.get("headline"))
            for s in stories[:3]
        )
        if isinstance(f, str) and f.strip()
    ]

    text_blob = " ".join(facts).lower()
    is_cpi = any(k in text_blob for k in ["cpi", "inflation", "consumer prices"])
    is_rates = any(k in text_blob for k in ["rates", "fed", "fomc", "policy"])
    is_jobs = any(k in text_blob for k in ["jobs", "employment", "labor"])

    seg_id = _gen_id("seg_macro")
    seed = _seed_from_facts(facts, "macro")

    thesis = _pick_template(MACRO_THESIS_TEMPLATES, seed)
    implication = _pick_template(MACRO_IMPL_TEMPLATES, seed)

    if is_cpi:
        implication = "Inflation signals look steadier, but the market is still waiting for confirmation that policy pressure is actually easing."
    elif is_rates:
        implication = "Rate expectations feel priced in, but markets remain hesitant to commit until the policy path is forced by data."
    elif is_jobs:
        implication = "Labor resilience supports confidence, but it can also delay policy flexibility if inflation re-accelerates."

    if numeric_context:
        phrase = _numeric_phrase(numeric_context)
        if phrase:
            thesis = f"{thesis} {phrase}"

    if signal_context:
        for sig in signal_context:
            if sig.get("confidence", 0) < 0.7:
                continue
            if sig.get("signal_type") in {"accumulation", "distribution"}:
                implication = f"{implication} Positioning suggests participants are preparing for outcomes, not reacting to headlines."
                break

    heat_val = _clamp(sum(_heat(s) for s in stories) / max(len(stories), 1))

    return Segment(
        segment_id=seg_id,
        segment_type="macro",
        domain="macro",
        thesis=thesis,
        facts=facts,
        implication=implication,
        heat=heat_val,
        source_count=len(stories),
        ts=_now(),
        anchor_plan=_anchor_plan("macro"),
        pd_hints={
            "allow_discussion": True,
            "allow_humor": False,
            "max_runtime_sec": 90,
            "angle_mode": _choose_angle("macro", stories),
            "vulnerability": "If credit conditions tighten faster than policy adapts, confidence breaks in flows, not headlines.",
            "counter_force": "Markets may appear calm even while funding conditions worsen.",
            "is_spine": True,
            "thread_id": _thread_id_for_stories("macro", stories),
        },
    )


def synthesize_market_segment(
    stories,
    *,
    numeric_context: Dict[str, Any] | None = None,
    signal_context: List[Dict[str, Any]] | None = None,
    domain_override: str = "markets"
):
    facts = []
    chip_numeric_hook = None

    for s in stories[:5]:
        md = s.get("market_data")
        if not isinstance(md, dict):
            continue
        symbol = md.get("symbol") or md.get("token") or md.get("ticker")
        price = md.get("price_usd")
        change = md.get("change_24h_pct")
        if symbol and price is not None and change is not None:
            facts.append(f"{symbol} ${price:.2f} ({change:+.2f}% 24h)")
            if chip_numeric_hook is None:
                try:
                    pct = float(change)
                    chip_numeric_hook = {
                        "label": "market_move",
                        "value": f"{pct:+.2f}%",
                        "spoken": f"{symbol} is {'up' if pct > 0 else 'down'} about {abs(pct):.0f} percent",
                        "domain": domain_override
                    }
                except Exception:
                    pass

    if not facts:
        facts = [
            f for f in (
                (s.get("summary") or s.get("headline"))
                for s in stories[:3]
            )
            if isinstance(f, str) and f.strip()
        ]

    seg_id = _gen_id("seg_market")
    seed = _seed_from_facts(facts, domain_override)

    if domain_override == "culture":
        thesis = _pick_template(CULTURE_THESIS_TEMPLATES, seed)
        implication = _pick_template(CULTURE_IMPL_TEMPLATES, seed)
    else:
        thesis = _pick_template(MARKETS_THESIS_TEMPLATES, seed)
        implication = _pick_template(MARKETS_IMPL_TEMPLATES, seed)

    if numeric_context:
        phrase = _numeric_phrase(numeric_context)
        if phrase:
            thesis = f"{thesis} {phrase}"

    if signal_context:
        sig_phrase = _signal_phrase(signal_context)
        if sig_phrase:
            implication = sig_phrase

    heat_val = _clamp(sum(_heat(s) for s in stories) / max(len(stories), 1))

    seg = Segment(
        segment_id=seg_id,
        segment_type="market" if domain_override != "culture" else "culture",
        domain=domain_override,
        thesis=thesis,
        facts=facts,
        implication=implication,
        heat=heat_val,
        source_count=len(stories),
        ts=_now(),
        anchor_plan=_anchor_plan(domain_override),
        pd_hints={
            "allow_discussion": True,
            "allow_humor": domain_override == "culture",
            "max_runtime_sec": 90 if domain_override == "markets" else 70,
            "angle_mode": _choose_angle(domain_override, stories),
            "vulnerability": "If the move is attention-driven, it can reverse faster than liquidity can absorb.",
            "counter_force": "Narrative strength can persist longer than structural support suggests.",
            "is_spine": domain_override in {"markets", "onchain"},
            "thread_id": _thread_id_for_stories(domain_override, stories),
        },
    )

    if chip_numeric_hook:
        seg.pd_hints["chip_numeric_hook"] = chip_numeric_hook

    return seg


def synthesize_trending_segment(
    stories,
    *,
    numeric_context: Dict[str, Any] | None = None,
    signal_context: List[Dict[str, Any]] | None = None
):
    symbols = []
    for s in stories:
        for sym in _story_assets(s):
            if sym not in symbols:
                symbols.append(sym)
            if len(symbols) >= 5:
                break
        if len(symbols) >= 5:
            break

    seg_id = _gen_id("seg_trend")
    facts = [f"{sym} trending across attention channels" for sym in symbols]

    seed = _seed_from_facts(facts, "trend")
    thesis = _pick_template(TREND_THESIS_TEMPLATES, seed)
    implication = _pick_template(TREND_IMPL_TEMPLATES, seed)

    if numeric_context:
        phrase = _numeric_phrase(numeric_context)
        if phrase:
            thesis = f"{thesis} {phrase}"

    if signal_context:
        sig_phrase = _signal_phrase(signal_context)
        if sig_phrase:
            implication = sig_phrase

    return Segment(
        segment_id=seg_id,
        segment_type="trend",
        domain="markets",
        thesis=thesis,
        facts=facts,
        implication=implication,
        heat=_clamp(sum(_heat(s) for s in stories) / max(len(stories), 1)),
        source_count=len(stories),
        ts=_now(),
        anchor_plan=_anchor_plan("markets"),
        pd_hints={
            "allow_discussion": True,
            "allow_humor": True,
            "max_runtime_sec": 60,
            "angle_mode": _choose_angle("markets", stories),
            "vulnerability": "If attention breaks, the unwind is fast and correlated.",
            "counter_force": "Crowd momentum can extend longer than expected.",
            "thread_id": _thread_id_for_stories("markets", stories),
        },
    )


def synthesize_context_segment(
    *,
    numeric_context: Dict[str, Any] | None,
    signal_context: List[Dict[str, Any]] | None,
    anchor_memory: Dict[str, Any],
    toknclaw_memory: Dict[str, Any] | None = None,
    toknclaw_deltas: Dict[str, Any] | None = None
) -> Segment:
    seg_id = _gen_id("seg_context")
    seed = _seed_from_facts([], "context")
    thesis = _pick_template(CONTEXT_THESIS_TEMPLATES, seed)
    implication = _pick_template(CONTEXT_IMPL_TEMPLATES, seed)

    if signal_context:
        for sig in signal_context:
            if sig.get("confidence", 0) < 0.7:
                continue
            stype = sig.get("signal_type")
            if stype == "accumulation":
                thesis = "Stepping back, markets look calm on the surface while positioning quietly builds."
                implication = "That kind of setup often develops before direction becomes obvious."
                break
            if stype == "distribution":
                thesis = "Stepping back, stability in price can mask a shift in underlying positioning."
                implication = "These environments can change character quickly once confidence fades."
                break
            if stype in {"capital_rotation", "liquidity_migration"}:
                thesis = "Stepping back, capital appears to be moving internally rather than entering or exiting risk."
                implication = "That usually signals uncertainty about where leadership comes next."
                break

    if numeric_context:
        eth = numeric_context.get("chains", {}).get("ethereum")
        if eth:
            tx_trend = eth.get("activity", {}).get("tx_trend")
            if tx_trend == "up":
                implication += " Activity is picking up even without strong price follow-through."

    if anchor_memory.get("open_threads"):
        implication += " Several broader themes we’ve been tracking remain unresolved."

    if isinstance(toknclaw_memory, dict):
        exch_trend = toknclaw_memory.get("exchange_flow_trend")
        whale_trend = toknclaw_memory.get("whale_activity_trend")
        liq_trend = toknclaw_memory.get("liquidation_trend")

        if exch_trend == "rising":
            implication += " Exchange flows have been building across recent cycles."
        if whale_trend == "rising":
            implication += " Whale activity has also been rising, which suggests larger participants are active."
        if liq_trend == "rising":
            implication += " Liquidation pressure is also increasing, which raises the risk of forced moves."

    if isinstance(toknclaw_deltas, dict):
        inflows = (toknclaw_deltas.get("exchange_inflows_usd") or {}).get("absolute_change")
        if isinstance(inflows, (int, float)) and inflows > 0:
            implication += " Flow pressure is increasing relative to the previous cycle."

    return Segment(
        segment_id=seg_id,
        segment_type="context",
        domain="general",
        thesis=thesis,
        facts=[],
        implication=implication.strip(),
        heat=5.0,
        source_count=0,
        ts=_now(),
        anchor_plan=_anchor_plan("general"),
        pd_hints={
            "allow_discussion": True,
            "allow_humor": False,
            "max_runtime_sec": 70,
            "is_filler": True,
            "angle_mode": "Liquidity-rotation lens (capital moving internally vs entering/exiting)",
            "vulnerability": "If the market misprices fragility, the unwind is faster than the buildup.",
            "counter_force": "Surface stability can persist until it suddenly doesn’t.",
            "thread_id": "closing_context",
        },
    )

# ============================================================
# DOMAIN CHAPTER CONTEXT
# ============================================================

def build_domain_chapters(segments: List[Segment]) -> Dict[str, Dict[str, Any]]:
    chapters: Dict[str, Dict[str, Any]] = {}
    for seg in segments:
        domain = seg.domain
        chapter = chapters.setdefault(domain, {
            "domain": domain,
            "segment_count": 0,
            "themes": set(),
            "theses": [],
        })
        chapter["segment_count"] += 1
        chapter["theses"].append(seg.thesis)

        blob = f"{seg.thesis} {seg.implication}".lower()
        for k in ("price", "liquidity", "flows", "position", "risk", "regulation", "credit", "sentiment", "meme"):
            if k in blob:
                chapter["themes"].add(k)

    for chapter in chapters.values():
        chapter["themes"] = sorted(chapter["themes"])
        chapter["summary"] = (
            f"{chapter['segment_count']} segment(s) covering "
            f"{', '.join(chapter['themes']) or 'general conditions'}."
        )

    return chapters

# ============================================================
# CROSS-SEGMENT INTERACTION INJECTION
# ============================================================

def _inject_cross_segment_context(seg_dicts: List[Dict[str, Any]]) -> None:
    for idx in range(1, len(seg_dicts)):
        prev = seg_dicts[idx - 1]
        cur = seg_dicts[idx]

        prev_domain = prev.get("domain", "general")
        prev_thesis = (prev.get("thesis") or "").strip()
        prev_imp = (prev.get("implication") or "").strip()

        cur_hints = cur.get("pd_hints", {}) or {}

        cur_hints["context_injection"] = (
            f"Acknowledge the prior {prev_domain.upper()} point in one line, "
            f"then either challenge it or extend it.\n"
            f"Prior thesis: {prev_thesis}\n"
            f"Prior implication: {prev_imp}\n"
            f"Use your domain lens; do not repeat the prior lines."
        )

        cur_hints["show_index"] = idx
        cur["pd_hints"] = cur_hints

# ============================================================
# MAIN SYNTHESIS LOGIC
# ============================================================

def synthesize_segments(
    stories: List[Dict[str, Any]],
    *,
    numeric_context: Dict[str, Any] | None = None,
    signal_context: List[Dict[str, Any]] | None = None
) -> List[Dict[str, Any]]:

    if not isinstance(stories, list):
        return []

    stories = [_normalize_story(s) for s in stories if isinstance(s, dict)]
    if not stories:
        return []

    print(f"[ESL] Starting synthesis with {len(stories)} stories")

    context_map: Dict[str, str] = {}
    if ENABLE_GROK_CONTEXT:
        try:
            raw = generate_context_for_clusters(stories)
            if isinstance(raw, dict):
                context_map = raw
        except Exception:
            context_map = {}

    by_domain = _build_domain_index(stories)
    segments: List[Segment] = []

    toknclaw_memory = _extract_toknclaw_memory(stories)
    toknclaw_deltas = _extract_toknclaw_deltas(stories)
    pressure = _signal_pressure(stories)

    def _inject_context(seg: Segment, domain_stories: List[Dict[str, Any]]):
        if ENABLE_GROK_CONTEXT:
            seg.pd_hints["editorial_context"] = context_map.get(seg.segment_id, "")
        if numeric_context:
            seg.pd_hints["numeric_context"] = numeric_context
        if signal_context:
            seg.pd_hints["signal_context"] = signal_context

        seg.pd_hints["toknclaw_memory"] = toknclaw_memory
        seg.pd_hints["toknclaw_deltas"] = toknclaw_deltas
        seg.pd_hints["signal_pressure"] = pressure
        seg.pd_hints["anchor_memory"] = load_anchor_memory(seg.anchor_plan.get("primary", "chip"))

        # Signals are primary narrative drivers: boost heat where relevant
        domain_assets = set()
        for ds in domain_stories[:10]:
            for a in _story_assets(ds):
                domain_assets.add(a)

        boost = 0.0
        counts = pressure["counts"]

        if seg.domain == "onchain":
            boost += counts.get("whale_transfer", 0) * 0.5
            boost += counts.get("exchange_inflow", 0) * 0.6
            boost += counts.get("defi_liquidation", 0) * 0.7
        elif seg.domain == "markets":
            boost += counts.get("exchange_inflow", 0) * 0.4
            boost += counts.get("exchange_outflow", 0) * 0.3
        elif seg.domain == "defi":
            boost += counts.get("defi_liquidation", 0) * 0.8

        if domain_assets:
            seg.heat = _clamp(seg.heat + boost)

    # 1. MARKET OPEN
    market_stories = by_domain.get("markets", [])
    if market_stories:
        seg = synthesize_market_segment(
            market_stories[:12],
            numeric_context=numeric_context,
            signal_context=signal_context,
            domain_override="markets"
        )
        _inject_context(seg, market_stories[:12])
        segments.append(seg)
        print("[ESL] Added market_open segment")

    # 2. ONCHAIN DESK
    onchain_stories = by_domain.get("onchain", [])
    if onchain_stories:
        seg = synthesize_market_segment(
            onchain_stories[:10],
            numeric_context=numeric_context,
            signal_context=signal_context,
            domain_override="onchain"
        )
        seg.segment_type = "onchain_desk"
        seg.pd_hints["vulnerability"] = "If flow strength is leverage-driven, it can unwind violently."
        seg.pd_hints["counter_force"] = "On-chain signals can lead price, but also fake-out under stress."
        _inject_context(seg, onchain_stories[:10])
        segments.append(seg)
        print("[ESL] Added onchain_desk segment")

    # 3. MACRO / REGULATION
    macro_stories = by_domain.get("macro", []) + by_domain.get("regulation", []) + by_domain.get("legal", [])
    if macro_stories:
        seg = synthesize_macro_segment(
            macro_stories[:10],
            numeric_context=numeric_context,
            signal_context=signal_context
        )
        _inject_context(seg, macro_stories[:10])
        segments.append(seg)
        print("[ESL] Added macro/regulation segment")

    # 4. SECTOR / DEFI / AI
    sector_pool = by_domain.get("defi", []) + by_domain.get("ai", [])
    if sector_pool:
        domain_override = "defi" if by_domain.get("defi") else "ai"
        seg = synthesize_market_segment(
            sector_pool[:10],
            numeric_context=numeric_context,
            signal_context=signal_context,
            domain_override=domain_override
        )
        if domain_override == "defi":
            seg.pd_hints["vulnerability"] = "If incentives flip, the flow can reverse quickly."
            seg.pd_hints["counter_force"] = "DeFi strength can persist even during broader risk-off."
        _inject_context(seg, sector_pool[:10])
        segments.append(seg)
        print("[ESL] Added sector segment")

    # 5. CULTURE / SENTIMENT / MEMECOIN PULSE
    culture_pool = by_domain.get("culture", []) + by_domain.get("sentiment", []) + by_domain.get("retail", [])
    if culture_pool:
        seg = synthesize_market_segment(
            culture_pool[:10],
            numeric_context=numeric_context,
            signal_context=signal_context,
            domain_override="culture"
        )
        seg.segment_type = "culture_pulse"
        seg.pd_hints["vulnerability"] = "If the crowd signal breaks, meme leadership tends to unwind quickly."
        seg.pd_hints["counter_force"] = "Retail narrative energy can still lead price longer than institutions expect."
        _inject_context(seg, culture_pool[:10])
        segments.append(seg)
        print("[ESL] Added culture_pulse segment")
    else:
        trending_candidates = [
            s for s in market_stories
            if _is_trending(s)
        ]
        if trending_candidates:
            seg = synthesize_trending_segment(
                trending_candidates[:8],
                numeric_context=numeric_context,
                signal_context=signal_context
            )
            _inject_context(seg, trending_candidates[:8])
            segments.append(seg)
            print("[ESL] Added trending fallback segment")

    # 6. CONTEXT / CLOSE
    filler = synthesize_context_segment(
        numeric_context=numeric_context,
        signal_context=signal_context,
        anchor_memory=load_anchor_memory("chip"),
        toknclaw_memory=toknclaw_memory,
        toknclaw_deltas=toknclaw_deltas
    )
    segments.append(filler)
    print("[ESL] Added context/close segment")

    # Diversity guardrail
    filtered_segments: List[Segment] = []
    domain_counts: Dict[str, int] = {}

    for seg in segments:
        domain_counts.setdefault(seg.domain, 0)
        if domain_counts[seg.domain] >= MAX_SEGMENTS_PER_DOMAIN:
            continue
        filtered_segments.append(seg)
        domain_counts[seg.domain] += 1
        if len(filtered_segments) >= MAX_TOTAL_SEGMENTS:
            break

    segments = filtered_segments

    if not segments:
        raise RuntimeError("ESL produced no segments")

    domain_chapters = build_domain_chapters(segments)
    for seg in segments:
        seg.pd_hints["chapter_context"] = domain_chapters.get(seg.domain, {})

    estimated_runtime = _estimate_runtime(segments)
    print(f"[ESL] Estimated runtime: {estimated_runtime} seconds")

    seg_dicts = [_apply_pd_fields(s.to_dict()) for s in segments]
    _inject_cross_segment_context(seg_dicts)

    return seg_dicts

# ============================================================
# CLI EXECUTION
# ============================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", default="/opt/toknnews/data/rolling_stories.json")
    parser.add_argument("--outfile", default="/tmp/synth_output.json")
    args = parser.parse_args()

    raw = json.loads(Path(args.infile).read_text())
    segments = synthesize_segments(raw, numeric_context={}, signal_context=[])

    Path(args.outfile).write_text(json.dumps(segments, indent=2))
    print(f"[✓] Wrote {len(segments)} segments -> {args.outfile}")
