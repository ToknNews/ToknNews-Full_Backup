#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝
╔══════════════════════════════════════════════════════════════════════════════╗
║ TOKNNEWS — memecoin_engine.py                                                ║
║ Deterministic Solana memecoin signal normalizer and daily segment builder.   ║
╚══════════════════════════════════════════════════════════════════════════════╝

File purpose
------------
This module consumes media_view-style JSON and produces a deterministic
memecoin_daily.json artifact for editorial use.

Goals
-----
- Reduce repeated Solana mint spam
- Resolve cleaner project identity from noisy story items
- Score memecoins by persistence, source diversity, and traction hints
- Select:
    - top memecoin of the day
    - funniest name of the day
    - survivor set
    - controlled meme segment candidates

Design rules
------------
- No LLM dependency
- No third-party package dependency
- Explicit CLI input/output paths
- Production-safe: never mutates upstream input
- Broad parser: tolerates multiple media_view shapes

Usage
-----
python3 /opt/toknnews/backend/memecoin_engine.py \
  --input /absolute/path/to/media_view.json \
  --output /absolute/path/to/memecoin_daily.json

Exit codes
----------
0 = success
1 = input or parsing failure
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

# -----------------------------
# BAD NAME FILTERS
# -----------------------------
GENERIC_NAME_PATTERNS = [
    "trending solana memecoin",
    "pump.fun token launch",
    "new token launch",
    "memecoin #",
    "token launch detected",
]

SOLANA_HINTS = {
    "solana",
    "sol",
    "pump.fun",
    "pumpfun",
    "raydium",
    "jupiter",
    "meteora",
    "orca",
    "photon",
    "dexscreener",
}

MEME_HINTS = {
    "memecoin",
    "meme coin",
    "meme",
    "shitcoin",
    "pump.fun",
    "pumpfun",
    "launch",
    "cto",
}

FUNNY_NAME_TERMS = {
    "fart",
    "butt",
    "pepe",
    "dog",
    "cat",
    "bonk",
    "goat",
    "toad",
    "giga",
    "chad",
    "wojak",
    "retardio",
    "jeet",
    "ngmi",
    "wen",
    "moon",
    "pump",
    "dump",
    "bread",
    "banana",
    "pickle",
    "burrito",
    "hamster",
    "pengu",
    "yolo",
}

BORING_NAME_TERMS = {
    "token",
    "coin",
    "official",
    "version",
    "v2",
    "v3",
    "new",
    "launch",
}

# -----------------------------
# TOKEN REGISTRY (LOCAL FALLBACK)
# -----------------------------
KNOWN_TOKENS = {
    "So11111111111111111111111111111111111111112": {
        "name": "Solana",
        "symbol": "SOL",
        "type": "base"
    }
}

# -----------------------------
# INVALID ENTITY FILTERS
# -----------------------------
INVALID_ENTITY_TERMS = [
    "alpha",
    "entry",
    "signal",
    "setup",
    "strategy",
    "opportunity",
    "rotation",
]

BASE_TOKENS = {
    "sol",
    "solana",
    "so11111111111111111111111111111111111111112",
}

# -----------------------------
# ENTITY RESOLUTION
# -----------------------------
def resolve_token_identity(mint, name, symbol):
    """
    Resolve token identity deterministically.
    """

    if mint and mint in KNOWN_TOKENS:
        data = KNOWN_TOKENS[mint]
        return data["name"], data["symbol"], data["type"]

    # reject obvious garbage names
    if name:
        text = name.lower()
        if any(x in text for x in [
            "trending",
            "token launch",
            "memecoin #",
            "pump.fun"
        ]):
            return None, None, "invalid"

    return name, symbol, "unknown"


def is_invalid_entity(name, symbol, mint):
    text = f"{name or ''} {symbol or ''} {mint or ''}".lower()

    # ❌ base tokens
    if any(base in text for base in BASE_TOKENS):
        return True

    # ❌ signal-type entities
    if any(term in text for term in INVALID_ENTITY_TERMS):
        return True

    return False

MINT_RE = re.compile(r"\b[1-9A-HJ-NP-Za-km-z]{32,44}\b")
URL_RE = re.compile(r"https?://\S+")
SYMBOL_RE = re.compile(r"\$([A-Za-z][A-Za-z0-9]{1,9})\b")
ALL_CAPS_RE = re.compile(r"\b[A-Z][A-Z0-9]{1,9}\b")
NAME_QUOTE_RE = re.compile(r"['\"]([A-Za-z0-9][A-Za-z0-9\s\-\._]{1,40})['\"]")


@dataclass
class Mention:
    item_id: str
    timestamp: Optional[datetime]
    url: Optional[str]
    source_name: str
    headline: str
    summary: str
    raw_text: str
    mint: Optional[str]
    resolved_name: Optional[str]
    resolved_symbol: Optional[str]
    traction_hints: List[str] = field(default_factory=list)


@dataclass
class ProjectAggregate:
    project_id: str
    name: Optional[str]
    symbol: Optional[str]
    mint: Optional[str]
    chain: str
    classification: str
    mentions: List[Mention] = field(default_factory=list)
    novelty_flags: List[str] = field(default_factory=list)

    def add_mention(self, mention: Mention) -> None:
        self.mentions.append(mention)

    @property
    def appearance_count(self) -> int:
        return len(self.mentions)

    @property
    def unique_source_count(self) -> int:
        return len({m.source_name for m in self.mentions if m.source_name})

    @property
    def first_seen(self) -> Optional[datetime]:
        times = [m.timestamp for m in self.mentions if m.timestamp is not None]
        return min(times) if times else None

    @property
    def last_seen(self) -> Optional[datetime]:
        times = [m.timestamp for m in self.mentions if m.timestamp is not None]
        return max(times) if times else None

    @property
    def timespan_hours(self) -> float:
        if self.first_seen is None or self.last_seen is None:
            return 0.0
        delta = self.last_seen - self.first_seen
        return round(delta.total_seconds() / 3600.0, 2)

    @property
    def sample_headlines(self) -> List[str]:
        seen = []
        for mention in self.mentions:
            text = normalize_space(mention.headline)
            if text and text not in seen:
                seen.append(text)
            if len(seen) >= 3:
                break
        return seen

    @property
    def sample_urls(self) -> List[str]:
        seen = []
        for mention in self.mentions:
            if mention.url and mention.url not in seen:
                seen.append(mention.url)
            if len(seen) >= 5:
                break
        return seen

    @property
    def resolved_mentions(self) -> List[str]:
        seen = []
        for mention in self.mentions:
            for candidate in [mention.resolved_name, mention.resolved_symbol]:
                if candidate and candidate not in seen:
                    seen.append(candidate)
        return seen[:8]

    @property
    def traction_terms(self) -> Counter:
        counter: Counter = Counter()
        for mention in self.mentions:
            counter.update(mention.traction_hints)
        return counter

def is_invalid_entity(name: Optional[str], symbol: Optional[str], mint: Optional[str]) -> bool:
    text = f"{name or ''} {symbol or ''} {mint or ''}".lower()

    # ❌ filter base chain token
    if any(base in text for base in BASE_TOKENS):
        return True

    # ❌ filter signal-type names
    if any(term in text for term in INVALID_ENTITY_TERMS):
        return True

    return False

def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "")).strip()


def safe_lower(value: Optional[str]) -> str:
    return (value or "").strip().lower()


def to_iso(dt: Optional[datetime]) -> Optional[str]:
    if dt is None:
        return None
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_timestamp(value: Any) -> Optional[datetime]:
    if value is None:
        return None

    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(float(value), tz=timezone.utc)
        except Exception:
            return None

    if not isinstance(value, str):
        return None

    raw = value.strip()
    if not raw:
        return None

    raw = raw.replace("Z", "+00:00")
    for candidate in [raw]:
        try:
            dt = datetime.fromisoformat(candidate)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            pass

    datetime_formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
        "%a, %d %b %Y %H:%M:%S %z",
    ]
    for fmt in datetime_formats:
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except Exception:
            continue

    return None


def coerce_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def deep_get(obj: Dict[str, Any], paths: Sequence[Sequence[str]]) -> Optional[Any]:
    for path in paths:
        current: Any = obj
        ok = True
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                ok = False
                break
        if ok and current not in (None, ""):
            return current
    return None


def flatten_story_items(payload: Any) -> List[Dict[str, Any]]:
    """
    Custom extractor for TOKNNEWS media_view structure.

    Priority:
    1. channel_payloads.broadcast (cleanest, deduped)
    2. top_stories
    3. segments.*.cards

    Avoid:
    - website duplication
    - newsletter duplication
    - entity-only lists
    """

    items: List[Dict[str, Any]] = []

    if not isinstance(payload, dict):
        return items

    # -----------------------------
    # 1. PRIMARY: broadcast payload
    # -----------------------------
    broadcast = (
        payload.get("channel_payloads", {})
        .get("broadcast", {})
    )

    if isinstance(broadcast, dict):
        for key, value in broadcast.items():
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        items.append(item)

    # -----------------------------
    # 2. FALLBACK: top_stories
    # -----------------------------
    top_stories = payload.get("top_stories")
    if isinstance(top_stories, list):
        for item in top_stories:
            if isinstance(item, dict):
                items.append(item)

    # -----------------------------
    # 3. SEGMENTS: cards only
    # -----------------------------
    segments = payload.get("segments", {})
    if isinstance(segments, dict):
        for seg in segments.values():
            if isinstance(seg, dict):
                cards = seg.get("cards")
                if isinstance(cards, list):
                    for item in cards:
                        if isinstance(item, dict):
                            items.append(item)

    return items

def item_text_blob(item: Dict[str, Any]) -> str:
    parts: List[str] = []

    def add(value: Any) -> None:
        if isinstance(value, str) and value.strip():
            parts.append(value.strip())

    add(deep_get(item, [["title"], ["headline"], ["name"]]))
    add(deep_get(item, [["summary"], ["description"], ["dek"], ["excerpt"]]))
    add(deep_get(item, [["content"], ["body"], ["text"]]))

    entities = item.get("entities")
    if isinstance(entities, list):
        for entity in entities:
            if isinstance(entity, dict):
                add(entity.get("name"))
                add(entity.get("symbol"))
                add(entity.get("ticker"))

    tags = item.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            add(str(tag))

    metadata = item.get("metadata")
    if isinstance(metadata, dict):
        for key in ["name", "symbol", "ticker", "protocol", "chain", "category"]:
            add(metadata.get(key))

    text = " | ".join(parts)
    return normalize_space(text)


def detect_source_name(item: Dict[str, Any]) -> str:
    source_value = deep_get(
        item,
        [
            ["source"],
            ["source_name"],
            ["publisher"],
            ["site_name"],
            ["metadata", "source"],
            ["metadata", "publisher"],
        ],
    )
    if isinstance(source_value, dict):
        source_value = source_value.get("name") or source_value.get("title")
    return normalize_space(str(source_value or "unknown"))[:80]


def detect_url(item: Dict[str, Any]) -> Optional[str]:
    value = deep_get(
        item,
        [
            ["url"],
            ["link"],
            ["article_url"],
            ["source_url"],
            ["metadata", "url"],
        ],
    )
    if isinstance(value, str) and value.startswith("http"):
        return value.strip()
    blob = item_text_blob(item)
    match = URL_RE.search(blob)
    return match.group(0) if match else None


def detect_timestamp(item: Dict[str, Any]) -> Optional[datetime]:
    value = deep_get(
        item,
        [
            ["published_at"],
            ["timestamp"],
            ["time"],
            ["created_at"],
            ["updated_at"],
            ["article", "published_at"],
            ["metadata", "published_at"],
        ],
    )
    return parse_timestamp(value)


def detect_headline(item: Dict[str, Any]) -> str:
    value = deep_get(item, [["title"], ["headline"], ["name"]])
    return normalize_space(str(value or ""))[:240]


def detect_summary(item: Dict[str, Any]) -> str:
    value = deep_get(item, [["summary"], ["description"], ["dek"], ["excerpt"]])
    return normalize_space(str(value or ""))[:500]


def detect_chain_hint(item: Dict[str, Any], blob: str) -> bool:
    candidates = [
        safe_lower(str(deep_get(item, [["chain"], ["network"], ["metadata", "chain"]]) or "")),
        safe_lower(blob),
    ]
    return any(hint in candidate for candidate in candidates for hint in SOLANA_HINTS)


def detect_meme_hint(item: Dict[str, Any], blob: str) -> bool:
    candidates = [
        safe_lower(str(deep_get(item, [["category"], ["type"], ["metadata", "category"]]) or "")),
        safe_lower(blob),
    ]
    return any(hint in candidate for candidate in candidates for hint in MEME_HINTS)


def extract_mint(blob: str) -> Optional[str]:
    matches = MINT_RE.findall(blob)
    if not matches:
        return None
    return max(matches, key=len)


def extract_symbol(item: Dict[str, Any], blob: str) -> Optional[str]:
    candidates: List[str] = []

    for path in [
        ["symbol"],
        ["ticker"],
        ["token_symbol"],
        ["metadata", "symbol"],
        ["metadata", "ticker"],
    ]:
        value = deep_get(item, [path])
        if isinstance(value, str):
            candidates.append(value)

    candidates.extend(SYMBOL_RE.findall(blob))
    candidates.extend(ALL_CAPS_RE.findall(blob))

    cleaned: List[str] = []
    for candidate in candidates:
        token = re.sub(r"[^A-Za-z0-9]", "", candidate).upper()
        if 2 <= len(token) <= 10:
            if token not in {"SOL", "USD", "USDT", "USDC", "DEX", "ETF", "SEC", "CPI"}:
                cleaned.append(token)

    return cleaned[0] if cleaned else None


def score_name_candidate(name: str) -> float:
    text = safe_lower(name)
    if not text:
        return -100.0

    score = 0.0
    length = len(text)

    if 3 <= length <= 18:
        score += 4.0
    elif length <= 28:
        score += 2.0
    else:
        score -= 2.0

    if " " in text:
        score += 1.0

    if re.search(r"[a-z]", text):
        score += 2.0

    if re.search(r"\d{4,}", text):
        score -= 2.0

    boring_hits = sum(1 for term in BORING_NAME_TERMS if term in text)
    funny_hits = sum(1 for term in FUNNY_NAME_TERMS if term in text)

    score += funny_hits * 1.5
    score -= boring_hits * 1.2

    if text.startswith("http"):
        score -= 10.0
    if MINT_RE.fullmatch(name.strip()):
        score -= 10.0

    return score

def is_generic_name(name: Optional[str]) -> bool:
    if not name:
        return True
    text = safe_lower(name)
    return any(pattern in text for pattern in GENERIC_NAME_PATTERNS)

def extract_name(item: Dict[str, Any], blob: str, symbol: Optional[str]) -> Optional[str]:
    candidates: List[str] = []

    for path in [
        ["name"],
        ["token_name"],
        ["project_name"],
        ["metadata", "name"],
        ["metadata", "token_name"],
    ]:
        value = deep_get(item, [path])
        if isinstance(value, str) and value.strip():
            candidates.append(value.strip())

    for match in NAME_QUOTE_RE.findall(blob):
        cleaned = normalize_space(match)
        if cleaned:
            candidates.append(cleaned)

    headline = detect_headline(item)
    if headline:
        candidates.append(headline)

    best_name = None
    best_score = -999.0

    for candidate in candidates:
        text = normalize_space(candidate)
        if not text:
            continue

        # Strip ticker-only noise from headlines.
        if symbol and text.upper() == symbol.upper():
            continue

        # Remove trailing separators and URLs.
        text = re.sub(r"https?://\S+", "", text).strip(" -:|,.;")
        current_score = score_name_candidate(text)

        if symbol and symbol.lower() in safe_lower(text):
            current_score += 1.0

        if current_score > best_score:
            best_score = current_score
            best_name = text

    return best_name


def canonical_project_id(name: Optional[str], symbol: Optional[str], mint: Optional[str]) -> str:
    if mint:
        return f"sol:{mint}"
    if symbol:
        return f"sol:{symbol.lower()}"
    if name:
        slug = re.sub(r"[^a-z0-9]+", "-", safe_lower(name)).strip("-")
        return f"sol:{slug}" if slug else "sol:unknown"
    return "sol:unknown"


def traction_hints_from_text(blob: str) -> List[str]:
    text = safe_lower(blob)
    hints: List[str] = []

    hint_terms = {
        "volume": ["volume", "turnover"],
        "rally": ["rally", "surge", "rip", "moon"],
        "selloff": ["dump", "selloff", "rug"],
        "liquidity": ["liquidity", "lp"],
        "whale": ["whale"],
        "trending": ["trending", "trend"],
        "fees": ["fees"],
        "holders": ["holders"],
        "marketcap": ["market cap", "mcap"],
        "cto": ["cto"],
        "listings": ["listing", "listed"],
    }

    for label, terms in hint_terms.items():
        if any(term in text for term in terms):
            hints.append(label)

    return hints


def is_memecoin_candidate(item: Dict[str, Any]) -> bool:
    blob = item_text_blob(item)
    has_solana = detect_chain_hint(item, blob)
    has_meme = detect_meme_hint(item, blob)

    if not has_solana:
        return False

    # Strong positive signals
    if has_meme:
        return True

    if "pump.fun" in safe_lower(blob):
        return True

    if extract_mint(blob) and ("launch" in safe_lower(blob) or "raydium" in safe_lower(blob)):
        return True

    symbol = extract_symbol(item, blob)
    name = extract_name(item, blob, symbol)
    if symbol and name:
        text = f"{safe_lower(name)} {safe_lower(symbol)}"
        if any(term in text for term in FUNNY_NAME_TERMS):
            return True

    return False


def build_mentions(items: List[Dict[str, Any]]) -> List[Mention]:
    mentions: List[Mention] = []

    for index, item in enumerate(items):
        if not isinstance(item, dict):
            continue

        if not is_memecoin_candidate(item):
            continue

        blob = item_text_blob(item)
        mint = extract_mint(blob)
        symbol = extract_symbol(item, blob)
        name = extract_name(item, blob, symbol)

        mention = Mention(
            item_id=str(deep_get(item, [["id"], ["story_id"], ["uuid"]]) or f"item_{index}"),
            timestamp=detect_timestamp(item),
            url=detect_url(item),
            source_name=detect_source_name(item),
            headline=detect_headline(item),
            summary=detect_summary(item),
            raw_text=blob,
            mint=mint,
            resolved_name=name,
            resolved_symbol=symbol,
            traction_hints=traction_hints_from_text(blob),
        )
        mentions.append(mention)

    return mentions


def aggregate_mentions(mentions: List[Mention]) -> Dict[str, ProjectAggregate]:
    projects: Dict[str, ProjectAggregate] = {}
    alias_map: Dict[str, str] = {}

    for mention in mentions:

        # -----------------------------
        # RESOLVE TOKEN IDENTITY FIRST
        # -----------------------------
        resolved_name, resolved_symbol, token_type = resolve_token_identity(
            mention.mint,
            mention.resolved_name,
            mention.resolved_symbol
        )

        # -----------------------------
        # EARLY FILTER (CRITICAL)
        # -----------------------------
        # ❌ remove base tokens (SOL etc.)
        if token_type == "base":
            continue

        # -----------------------------
        # BUILD PROJECT ID
        # -----------------------------
        project_id = canonical_project_id(
            name=resolved_name,
            symbol=resolved_symbol,
            mint=mention.mint,
        )

        # -----------------------------
        # ALIAS MAPPING (DEDUP LOGIC)
        # -----------------------------
        if mention.mint:
            mint_key = f"mint:{mention.mint}"
            if mint_key in alias_map:
                project_id = alias_map[mint_key]
            else:
                alias_map[mint_key] = project_id

        if resolved_symbol:
            sym_key = f"sym:{resolved_symbol.lower()}"
            if sym_key in alias_map and not mention.mint:
                project_id = alias_map[sym_key]
            else:
                alias_map.setdefault(sym_key, project_id)

        if resolved_name:
            name_key = f"name:{re.sub(r'[^a-z0-9]+', '-', safe_lower(resolved_name)).strip('-')}"
            if name_key in alias_map and not mention.mint:
                project_id = alias_map[name_key]
            else:
                alias_map.setdefault(name_key, project_id)

        # -----------------------------
        # CREATE PROJECT
        # -----------------------------
        if project_id not in projects:
            projects[project_id] = ProjectAggregate(
                project_id=project_id,
                name=resolved_name,
                symbol=resolved_symbol,
                mint=mention.mint,
                chain="solana",
                classification="memecoin",
            )

        project = projects[project_id]

        # -----------------------------
        # UPDATE BEST NAME / SYMBOL
        # -----------------------------
        if resolved_name and score_name_candidate(resolved_name) > score_name_candidate(project.name or ""):
            project.name = resolved_name

        if resolved_symbol and not project.symbol:
            project.symbol = resolved_symbol

        if mention.mint and not project.mint:
            project.mint = mention.mint

        # -----------------------------
        # ADD MENTION
        # -----------------------------
        project.add_mention(mention)

    return projects


def score_project(project: ProjectAggregate) -> Tuple[float, Dict[str, float]]:
    appearance_score = min(project.appearance_count * 4.0, 28.0)
    source_diversity_score = min(project.unique_source_count * 6.0, 24.0)
    timespan_score = min(project.timespan_hours * 1.5, 18.0)

    traction_counter = project.traction_terms
    traction_score = min(
        (
            traction_counter.get("volume", 0) * 3.0
            + traction_counter.get("trending", 0) * 2.5
            + traction_counter.get("liquidity", 0) * 2.0
            + traction_counter.get("holders", 0) * 2.0
            + traction_counter.get("marketcap", 0) * 1.5
        ),
        20.0,
    )

    name_quality_score = max(min(score_name_candidate(project.name or ""), 8.0), 0.0)

    penalty = 0.0

    # ❌ kill generic names
    if is_generic_name(project.name):
        penalty += 15.0

    # ❌ single-source spam
    if project.unique_source_count <= 1:
        penalty += 10.0

    # ❌ no persistence
    if project.timespan_hours == 0:
        penalty += 8.0

    # ❌ weak appearance
    if project.appearance_count < 3:
        penalty += 6.0

    # ❌ no name or symbol
    if not project.name and not project.symbol:
        penalty += 10.0

    total = round(
        appearance_score
        + source_diversity_score
        + timespan_score
        + traction_score
        + name_quality_score
        - penalty,
        2,
    )

    breakdown = {
        "appearance_score": round(appearance_score, 2),
        "source_diversity_score": round(source_diversity_score, 2),
        "timespan_score": round(timespan_score, 2),
        "traction_score": round(traction_score, 2),
        "name_quality_score": round(name_quality_score, 2),
    }
    return total, breakdown


def funny_score(project: ProjectAggregate) -> Tuple[float, List[str]]:
    text = f"{project.name or ''} {project.symbol or ''}".strip()
    lowered = safe_lower(text)

    score = 0.0
    reasons: List[str] = []

    funny_hits = [term for term in FUNNY_NAME_TERMS if term in lowered]
    for term in funny_hits[:4]:
        score += 3.0
        reasons.append(f"keyword_match:{term}")

    if 3 <= len(project.name or "") <= 14:
        score += 2.0
        reasons.append("short_memorable_name")

    if project.symbol and 3 <= len(project.symbol) <= 5:
        score += 1.0
        reasons.append("clean_symbol")

    if project.appearance_count >= 2:
        score += 1.5
        reasons.append("repeated_mentions")

    if project.unique_source_count >= 2:
        score += 1.5
        reasons.append("cross_source_presence")

    if not funny_hits:
        score -= 2.0

    return round(score, 2), reasons[:5]


def traction_label(project_score: float, appearances: int, unique_sources: int, timespan_hours: float) -> str:
    if project_score >= 70 and appearances >= 4 and unique_sources >= 3 and timespan_hours >= 6:
        return "high"
    if project_score >= 45 and appearances >= 3 and unique_sources >= 2:
        return "medium"
    return "low"


def stable_hash(value: str) -> str:
    return hashlib.sha1(value.encode("utf-8")).hexdigest()[:10]


def build_output(
    *,
    input_path: Path,
    items: List[Dict[str, Any]],
    projects: Dict[str, ProjectAggregate],
) -> Dict[str, Any]:
    ranked_rows: List[Dict[str, Any]] = []
    funny_rows: List[Tuple[str, float, List[str]]] = []

    ranked = []
    for project_id, project in projects.items():
        project_score, breakdown = score_project(project)
        name_funny_score, reasons = funny_score(project)
        ranked.append((project_id, project, project_score, breakdown, name_funny_score, reasons))

        # HARD FILTER: skip low-quality spam
        if project.unique_source_count < 2:
            continue

        if project.appearance_count < 3:
            continue

        if is_generic_name(project.name):
            continue
        # ❌ remove non-token entities
        if is_invalid_entity(project.name, project.symbol, project.mint):
            continue

    ranked.sort(key=lambda row: (row[2], row[4], row[1].appearance_count), reverse=True)

    top_project = ranked[0] if ranked else None
    funniest_project = max(ranked, key=lambda row: row[4], default=None)

    survivors: List[Dict[str, Any]] = []
    for project_id, project, project_score, _, name_funny_score, _ in ranked:
        label = traction_label(
            project_score=project_score,
            appearances=project.appearance_count,
            unique_sources=project.unique_source_count,
            timespan_hours=project.timespan_hours,
        )

        ranked_rows.append(
            {
                "project_id": project_id,
                "name": project.name,
                "symbol": project.symbol,
                "mint": project.mint,
                "score": project_score,
                "funny_score": name_funny_score,
                "appearance_count": project.appearance_count,
                "unique_source_count": project.unique_source_count,
                "timespan_hours": project.timespan_hours,
                "novelty_flags": project.novelty_flags,
                "sample_headlines": project.sample_headlines,
                "sample_urls": project.sample_urls,
            }
        )

        if label in {"high", "medium"}:
            survivors.append(
                {
                    "project_id": project_id,
                    "name": project.name,
                    "symbol": project.symbol,
                    "score": project_score,
                    "appearance_count": project.appearance_count,
                    "unique_source_count": project.unique_source_count,
                    "timespan_hours": project.timespan_hours,
                    "traction_label": label,
                }
            )

        funny_rows.append((project_id, name_funny_score, []))

    summary = {
        "items_scanned": len(items),
        "memecoin_candidates_found": sum(project.appearance_count for project in projects.values()),
        "deduped_projects": len(projects),
        "top_memecoin_id": top_project[0] if top_project else None,
        "funniest_name_id": funniest_project[0] if funniest_project else None,
        "meme_segment_recommended": bool(top_project and top_project[2] >= 35.0),
    }

    result: Dict[str, Any] = {
        "generated_at": to_iso(datetime.now(timezone.utc)),
        "source_file": str(input_path),
        "analysis_window": build_analysis_window(projects),
        "summary": summary,
        "top_memecoin_of_day": None,
        "funniest_name_of_day": None,
        "survivors": survivors[:5],
        "ranked_projects": ranked_rows[:20],
        "segment_candidates": [],
    }

    if top_project:
        project_id, project, project_score, breakdown, _, _ = top_project
        result["top_memecoin_of_day"] = {
            "project_id": project_id,
            "name": project.name,
            "symbol": project.symbol,
            "chain": project.chain,
            "classification": project.classification,
            "score": project_score,
            "score_breakdown": breakdown,
            "support": {
                "appearance_count": project.appearance_count,
                "unique_source_count": project.unique_source_count,
                "first_seen": to_iso(project.first_seen),
                "last_seen": to_iso(project.last_seen),
                "timespan_hours": project.timespan_hours,
                "resolved_mentions": project.resolved_mentions,
                "sample_urls": project.sample_urls,
            },
        }

    if funniest_project:
        project_id, project, _, _, fun_score, reasons = funniest_project
        result["funniest_name_of_day"] = {
            "project_id": project_id,
            "name": project.name,
            "symbol": project.symbol,
            "chain": project.chain,
            "funny_score": fun_score,
            "funny_reasons": reasons,
            "support": {
                "appearance_count": project.appearance_count,
                "unique_source_count": project.unique_source_count,
            },
        }

    if result["summary"]["meme_segment_recommended"]:
        included_ids: List[str] = []
        if top_project:
            included_ids.append(top_project[0])
        if funniest_project and funniest_project[0] not in included_ids:
            included_ids.append(funniest_project[0])

        result["segment_candidates"].append(
            {
                "segment_id": f"meme_daily_{stable_hash('|'.join(included_ids) or 'none')}",
                "title": "Meme Check",
                "angle": (
                    "One controlled meme block: strongest surviving name plus funniest "
                    "headline magnet, capped to avoid show takeover."
                ),
                "included_project_ids": included_ids,
            }
        )

    return result


def build_analysis_window(projects: Dict[str, ProjectAggregate]) -> Dict[str, Optional[str]]:
    all_first = [p.first_seen for p in projects.values() if p.first_seen is not None]
    all_last = [p.last_seen for p in projects.values() if p.last_seen is not None]
    start = min(all_first) if all_first else None
    end = max(all_last) if all_last else None
    return {
        "start": to_iso(start),
        "end": to_iso(end),
    }


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Deterministically normalize Solana memecoin noise into memecoin_daily.json."
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Absolute path to media_view.json input.",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Absolute path for memecoin_daily.json output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_path = Path(args.input).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()

    if not input_path.exists():
        print(f"ERROR: input file does not exist: {input_path}")
        return 1

    try:
        payload = load_json(input_path)
        items = flatten_story_items(payload)
        mentions = build_mentions(items)
        projects = aggregate_mentions(mentions)
        result = build_output(input_path=input_path, items=items, projects=projects)
        write_json(output_path, result)
    except Exception as exc:
        print(f"ERROR: memecoin engine failed: {exc}")
        return 1

    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
