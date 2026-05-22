#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS — ANCHOR AGENT ROUND v1.0
Pre-Broadcast Multi-Agent Discussion Engine

Purpose
-------
Runs a full pre-broadcast anchor discussion round before timeline assembly.

This module:
• loads structured dialogue blocks from ingest_brain
• fetches and digests raw URLs when available
• injects character persona and memory
• runs a collaborative Mode A roundtable across anchors
• supports OpenClaw-first generation, with OpenAI and deterministic fallback
• writes enriched dialogue blocks for downstream timeline building
• writes show-prep artifacts for promos, newsletter, and future verticals

Primary Inputs
--------------
• /opt/toknnews/data/stories/dialogue_blocks.json
• /opt/toknnews/data/stories/episode_context.json
• raw_url values embedded inside each block.context.raw_url

Primary Outputs
---------------
• /opt/toknnews/data/stories/anchor_rounds.json
• /opt/toknnews/data/stories/dialogue_blocks_agent.json
• /opt/toknnews/data/stories/show_prep.json

Design Notes
------------
• Mode A = collaborative shared discussion state
• OpenClaw-first adapter
• OpenAI fallback
• deterministic offline fallback
• future-ready for newsletter / social / promo verticals
• preserves original ingest output while adding agent-generated dialogue

Author: TOKN Systems
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import shlex
import subprocess
import time
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import requests  # type: ignore
except Exception:
    requests = None

try:
    from bs4 import BeautifulSoup  # type: ignore
except Exception:
    BeautifulSoup = None

try:
    import openai  # type: ignore

    openai.api_key = os.getenv("OPENAI_API_KEY")
    OPENAI_ENABLED = bool(os.getenv("OPENAI_API_KEY"))
except Exception:
    openai = None
    OPENAI_ENABLED = False

from backend.script_engine.character_brain.persona_loader import (
    build_persona_prompt_context,
    get_display_name,
    get_voice,
)
from backend.script_engine.character_brain.memory_engine import (
    get_anchor_history,
    get_callback_candidates,
    get_domain_heatmap,
    update_memory_with_episode,
    update_memory_with_story,
)


# ---------------------------------------------------------
# PATHS
# ---------------------------------------------------------

INPUT_DIALOGUE_BLOCKS = Path("/opt/toknnews/data/stories/dialogue_blocks.json")
INPUT_EPISODE_CONTEXT = Path("/opt/toknnews/data/stories/episode_context.json")

OUTPUT_ROUNDS = Path("/opt/toknnews/data/stories/anchor_rounds.json")
OUTPUT_AGENT_DIALOGUE = Path("/opt/toknnews/data/stories/dialogue_blocks_agent.json")
OUTPUT_SHOW_PREP = Path("/opt/toknnews/data/stories/show_prep.json")

TMP_ROUNDS = OUTPUT_ROUNDS.with_suffix(".tmp")
TMP_AGENT_DIALOGUE = OUTPUT_AGENT_DIALOGUE.with_suffix(".tmp")
TMP_SHOW_PREP = OUTPUT_SHOW_PREP.with_suffix(".tmp")

URL_CACHE_DIR = Path("/opt/toknnews/data/cache/url_digests")
URL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# GLOBAL SETTINGS
# ---------------------------------------------------------

AGENT_BACKEND = os.getenv("TOKN_AGENT_BACKEND", "openclaw").strip().lower()
OPENAI_MODEL = os.getenv("TOKN_AGENT_OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_TEMPERATURE = float(os.getenv("TOKN_AGENT_OPENAI_TEMPERATURE", "0.7"))
OPENAI_MAX_TOKENS = int(os.getenv("TOKN_AGENT_OPENAI_MAX_TOKENS", "220"))

# IMPORTANT:
# Use this to wire your exact OpenClaw CLI invocation without guessing.
# It must contain:
#   {agent}
#   {input_file}
# Example:
#   export TOKN_OPENCLAW_COMMAND_TEMPLATE='openclaw run --agent {agent} --json-input {input_file}'
OPENCLAW_COMMAND_TEMPLATE = os.getenv("TOKN_OPENCLAW_COMMAND_TEMPLATE", "").strip()

OPENCLAW_ENABLED = bool(shutil_which("openclaw"))
HTTP_TIMEOUT_SEC = int(os.getenv("TOKN_AGENT_HTTP_TIMEOUT_SEC", "15"))
MAX_BLOCKS = int(os.getenv("TOKN_AGENT_MAX_BLOCKS", "12"))
MAX_SOURCE_CHARS = int(os.getenv("TOKN_AGENT_MAX_SOURCE_CHARS", "5000"))
MAX_DIGEST_CHARS = int(os.getenv("TOKN_AGENT_MAX_DIGEST_CHARS", "2000"))
MAX_SHARED_NOTES = int(os.getenv("TOKN_AGENT_MAX_SHARED_NOTES", "12"))
GLOBAL_FALLBACK_MODE = os.getenv("TOKN_GLOBAL_FALLBACK_MODE", "0") == "1"
LATE_NIGHT_MODE = os.getenv("TOKN_LATE_NIGHT_MODE", "0") == "1"


# ---------------------------------------------------------
# BASIC HELPERS
# ---------------------------------------------------------

def shutil_which(binary: str) -> str:
    try:
        completed = subprocess.run(
            ["bash", "-lc", f"command -v {shlex.quote(binary)} || true"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return completed.stdout.strip()
    except Exception:
        return ""


def clean(value: Any) -> str:
    return "" if value is None else str(value).strip()


def safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def safe_list(value: Any) -> List[Any]:
    return value if isinstance(value, list) else []


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


def sanitize_tts(text: str) -> str:
    if not text:
        return ""
    out = clean(text)
    out = re.sub(r"\s{2,}", " ", out)
    return out.strip()


def atomic_write_json(path: Path, tmp_path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path.write_text(json.dumps(payload, indent=2))
    tmp_path.replace(path)


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    try:
        payload = json.loads(path.read_text())
        return payload
    except Exception:
        return default


def _emit_openclaw_event(event_type: str, payload: Dict[str, Any]) -> None:
    if os.getenv("TOKN_OPENCLAW_HOOK") == "1":
        try:
            print(f"[OPENCLAW] {event_type} :: {json.dumps(payload)[:500]}")
        except Exception:
            print(f"[OPENCLAW] {event_type}")


def _now_ts() -> float:
    return time.time()


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------
# DOMAIN / ANCHOR LOGIC
# ---------------------------------------------------------

DOMAIN_DEFAULT_PANEL = {
    "macro": ["chip", "bond", "cash"],
    "regulation": ["chip", "lawson", "bond"],
    "markets": ["chip", "cash", "bond"],
    "defi": ["chip", "reef", "ledger"],
    "onchain": ["chip", "ledger", "reef"],
    "culture": ["chip", "cash", "bitsy"],
    "news": ["chip", "bond", "lawson"],
    "general": ["chip", "bond", "cash"],
}

DOMAIN_TO_NORMALIZED = {
    "macro": "macro",
    "regulation": "regulation",
    "markets": "markets",
    "market": "markets",
    "crypto_major": "markets",
    "crypto_alt": "markets",
    "defi": "defi",
    "flows": "onchain",
    "onchain": "onchain",
    "crypto_culture": "culture",
    "culture": "culture",
    "sentiment": "culture",
    "news": "news",
    "general": "general",
}


def normalize_domain(domain: str) -> str:
    d = clean(domain).lower()
    return DOMAIN_TO_NORMALIZED.get(d, d if d else "general")


def build_anchor_panel(block: Dict[str, Any]) -> List[str]:
    domain = normalize_domain(clean(block.get("domain")))
    candidates = [clean(x).lower() for x in safe_list(block.get("anchor_candidates")) if clean(x)]
    if not candidates:
        candidates = DOMAIN_DEFAULT_PANEL.get(domain, DOMAIN_DEFAULT_PANEL["general"])[:]

    panel: List[str] = []

    if "chip" not in candidates:
        panel.append("chip")

    for name in candidates:
        if name not in panel:
            panel.append(name)

    default_panel = DOMAIN_DEFAULT_PANEL.get(domain, DOMAIN_DEFAULT_PANEL["general"])
    for name in default_panel:
        if name not in panel:
            panel.append(name)

    # Keep panel tight and useful
    if domain == "culture":
        panel = [x for x in panel if x not in {"lawson"}]

    return panel[:4]


def choose_turn_order(panel: List[str], domain: str) -> List[str]:
    """
    Shared discussion order.
    Chip hosts.
    Secondary anchors discuss.
    Chip closes.
    """
    domain = normalize_domain(domain)
    panel = unique_preserve([clean(x).lower() for x in panel if clean(x)])

    if "chip" not in panel:
        panel.insert(0, "chip")

    analysts = [x for x in panel if x != "chip"]
    if not analysts:
        analysts = ["bond"]

    if domain == "culture":
        analysts = [x for x in analysts if x in {"cash", "bitsy", "ivy", "bond"}] or analysts
    elif domain == "defi":
        analysts = [x for x in analysts if x in {"reef", "ledger", "cash", "bond"}] or analysts
    elif domain == "macro":
        analysts = [x for x in analysts if x in {"bond", "cash", "lawson"}] or analysts
    elif domain == "regulation":
        analysts = [x for x in analysts if x in {"lawson", "bond", "cash"}] or analysts

    order = ["chip"]
    order.extend(analysts[:2])
    order.append("chip")

    # Optional 5th turn when there is strong debate potential
    if len(analysts) > 1:
        order.append(analysts[0])

    return order[:5]


# ---------------------------------------------------------
# URL FETCH / DIGEST
# ---------------------------------------------------------

def _url_cache_path(url: str) -> Path:
    return URL_CACHE_DIR / f"{_hash_text(url)}.json"


def fetch_url_text(url: str) -> Dict[str, Any]:
    """
    Best-effort raw URL fetcher for source grounding.
    """
    url = clean(url)
    if not url:
        return {"url": "", "ok": False, "title": "", "text": "", "error": "missing_url"}

    cache_path = _url_cache_path(url)
    cached = load_json(cache_path, {})
    if safe_dict(cached).get("ok") and clean(safe_dict(cached).get("text")):
        return cached

    if requests is None:
        payload = {
            "url": url,
            "ok": False,
            "title": "",
            "text": "",
            "error": "requests_unavailable",
        }
        atomic_write_json(cache_path, cache_path.with_suffix(".tmp"), payload)
        return payload

    try:
        headers = {
            "User-Agent": "ToknNewsAnchorRound/1.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        resp = requests.get(url, timeout=HTTP_TIMEOUT_SEC, headers=headers)
        resp.raise_for_status()
        html = resp.text or ""

        title = ""
        text = ""

        if BeautifulSoup is not None:
            soup = BeautifulSoup(html, "html.parser")

            if soup.title:
                title = clean(soup.title.get_text(" ", strip=True))

            for tag in soup(["script", "style", "noscript"]):
                tag.extract()

            body_text = soup.get_text("\n", strip=True)
            lines = [clean(x) for x in body_text.splitlines() if clean(x)]
            text = "\n".join(lines)
        else:
            title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.I | re.S)
            if title_match:
                title = clean(re.sub(r"<[^>]+>", " ", title_match.group(1)))

            text = re.sub(r"<script.*?</script>", " ", html, flags=re.I | re.S)
            text = re.sub(r"<style.*?</style>", " ", text, flags=re.I | re.S)
            text = re.sub(r"<[^>]+>", " ", text)
            text = re.sub(r"\s{2,}", " ", text)

        text = clean(text)[:MAX_SOURCE_CHARS]

        payload = {
            "url": url,
            "ok": True,
            "title": title,
            "text": text,
            "error": "",
            "fetched_at": _now_ts(),
        }
        atomic_write_json(cache_path, cache_path.with_suffix(".tmp"), payload)
        return payload

    except Exception as e:
        payload = {
            "url": url,
            "ok": False,
            "title": "",
            "text": "",
            "error": clean(e),
        }
        atomic_write_json(cache_path, cache_path.with_suffix(".tmp"), payload)
        return payload


def build_source_digest(block: Dict[str, Any]) -> Dict[str, Any]:
    context = safe_dict(block.get("context"))
    raw_url = clean(context.get("raw_url"))
    title = clean(block.get("thesis"))
    summary = clean(block.get("implication"))

    fetched = fetch_url_text(raw_url) if raw_url else {"ok": False, "title": "", "text": "", "error": "no_url"}
    source_title = clean(fetched.get("title")) or title
    source_text = clean(fetched.get("text"))

    digest_parts: List[str] = []
    if source_title:
        digest_parts.append(f"TITLE: {source_title}")
    if summary:
        digest_parts.append(f"INGEST SUMMARY: {summary}")
    if source_text:
        digest_parts.append(f"SOURCE EXCERPT: {source_text[:MAX_DIGEST_CHARS]}")

    digest = "\n".join(digest_parts).strip()

    return {
        "raw_url": raw_url,
        "fetch_ok": bool(fetched.get("ok")),
        "source_title": source_title,
        "source_text": source_text,
        "source_digest": digest,
        "fetch_error": clean(fetched.get("error")),
    }


# ---------------------------------------------------------
# MEMORY / CONTINUITY
# ---------------------------------------------------------

def build_memory_context(speaker: str, domain: str, thread_id: str) -> Dict[str, Any]:
    anchor_history = get_anchor_history(speaker)
    callback_candidates = get_callback_candidates(limit=6)
    domain_heatmap = get_domain_heatmap()

    thread_rows: List[Dict[str, Any]] = []
    for row in callback_candidates:
        row = safe_dict(row)
        rid = clean(row.get("thread_id"))
        if not rid:
            continue
        if rid == clean(thread_id):
            thread_rows.append(row)
            continue
        if clean(row.get("domain")).lower() == clean(domain).lower():
            thread_rows.append(row)

    return {
        "anchor_history": anchor_history,
        "callback_candidates": thread_rows[:3],
        "domain_heat": safe_dict(domain_heatmap).get(clean(domain).lower(), {}),
    }


# ---------------------------------------------------------
# PROMPT BUILDING
# ---------------------------------------------------------

def build_shared_story_context(
    block: Dict[str, Any],
    episode_context: Dict[str, Any],
    source_digest: Dict[str, Any],
    shared_notes: List[Dict[str, Any]],
) -> Dict[str, Any]:
    context = safe_dict(block.get("context"))
    pd_hints = safe_dict(block.get("pd_hints"))
    editorial_hints = safe_dict(block.get("editorial_hints"))

    notes = []
    for row in shared_notes[-MAX_SHARED_NOTES:]:
        row = safe_dict(row)
        notes.append(
            {
                "speaker": clean(row.get("speaker")).lower(),
                "role": clean(row.get("role")).lower(),
                "stance": clean(row.get("stance")).lower(),
                "text": clean(row.get("text")),
            }
        )

    return {
        "narrative_id": clean(block.get("narrative_id")),
        "domain": normalize_domain(clean(block.get("domain"))),
        "raw_domain": clean(block.get("raw_domain") or block.get("domain")),
        "thesis": clean(block.get("thesis")),
        "implication": clean(block.get("implication")),
        "entities": [clean(x) for x in safe_list(block.get("entities")) if clean(x)],
        "signal_type": clean(context.get("signal_type")),
        "entity_domain": clean(context.get("entity_domain")),
        "supporting_signal_types": [clean(x) for x in safe_list(context.get("supporting_signal_types")) if clean(x)],
        "confidence": safe_float(context.get("confidence"), 0.0),
        "story_score": safe_float(context.get("story_score"), 0.0),
        "thread_id": clean(pd_hints.get("thread_id")),
        "debate_potential": bool(pd_hints.get("debate_potential")),
        "requires_numeric": bool(pd_hints.get("requires_numeric")),
        "segment_type": clean(pd_hints.get("segment_type") or "support"),
        "tone": clean(editorial_hints.get("tone") or "analytical"),
        "complexity": clean(editorial_hints.get("complexity") or "medium"),
        "episode_thesis": clean(episode_context.get("episode_thesis")),
        "signal_summary": clean(episode_context.get("signal_summary")),
        "risk_direction": clean(episode_context.get("risk_direction")),
        "dominant_assets": safe_list(episode_context.get("dominant_assets")),
        "source_digest": clean(source_digest.get("source_digest")),
        "raw_url": clean(source_digest.get("raw_url")),
        "shared_notes": notes,
    }


def build_role_instruction(
    speaker: str,
    turn_index: int,
    total_turns: int,
    panel: List[str],
    block: Dict[str, Any],
) -> Dict[str, str]:
    speaker = clean(speaker).lower()
    domain = normalize_domain(clean(block.get("domain")))
    pd_hints = safe_dict(block.get("pd_hints"))

    if turn_index == 0 and speaker == "chip":
        return {
            "role": "host_open",
            "stance": "frame",
            "instruction": (
                "Frame the segment for the audience, identify the real tension, and toss into analysis "
                "without repeating the summary verbatim."
            ),
        }

    if turn_index == total_turns - 2 and speaker == "chip":
        return {
            "role": "host_challenge",
            "stance": "challenge",
            "instruction": (
                "Challenge the panel. Surface the uncertainty, weak point, or missing variable."
            ),
        }

    if turn_index == total_turns - 1:
        return {
            "role": "final_take",
            "stance": "close",
            "instruction": (
                "Close with the most useful takeaway for viewers. No filler. No generic ending."
            ),
        }

    if speaker == "bond":
        return {
            "role": "macro_analyst",
            "stance": "skeptical" if bool(pd_hints.get("debate_potential")) else "measured",
            "instruction": "Analyze through liquidity, macro backdrop, rates, risk appetite, and durability.",
        }

    if speaker == "reef":
        return {
            "role": "defi_analyst",
            "stance": "opportunistic",
            "instruction": "Analyze through protocol traction, liquidity concentration, and onchain opportunity.",
        }

    if speaker == "ledger":
        return {
            "role": "onchain_analyst",
            "stance": "forensic",
            "instruction": "Analyze through flows, balances, transfer mechanics, wallets, and signal quality.",
        }

    if speaker == "lawson":
        return {
            "role": "policy_analyst",
            "stance": "cautious",
            "instruction": "Analyze through legal, compliance, precedent, and operational consequences.",
        }

    if speaker == "cash":
        return {
            "role": "markets_behavior_analyst",
            "stance": "behavioral",
            "instruction": "Analyze through positioning, trader psychology, retail behavior, and market reflexivity.",
        }

    if speaker == "ivy":
        return {
            "role": "sentiment_analyst",
            "stance": "human",
            "instruction": "Analyze through crowd psychology, behavior, incentives, and emotional cycles.",
        }

    if speaker == "bitsy":
        return {
            "role": "meta_interrupt",
            "stance": "meta",
            "instruction": "Be short, mischievous, and meta. Never analytical. Max 16 words.",
        }

    if speaker == "penny":
        return {
            "role": "human_interest_analyst",
            "stance": "accessible",
            "instruction": "Translate the story for a wider audience in plain English without dumbing it down.",
        }

    return {
        "role": "analyst",
        "stance": "neutral",
        "instruction": "Advance the segment with a useful, non-repetitive line.",
    }


def build_agent_prompt(
    speaker: str,
    role_spec: Dict[str, str],
    persona_context: Dict[str, Any],
    memory_context: Dict[str, Any],
    shared_story_context: Dict[str, Any],
) -> str:
    persona_lines = "\n".join(f"- {clean(x)}" for x in safe_list(persona_context.get("persona_lines"))[:10])
    phrasing = "\n".join(f"- {clean(x)}" for x in safe_list(persona_context.get("analysis_phrasing"))[:8])
    structures = "\n".join(f"- {clean(x)}" for x in safe_list(persona_context.get("analysis_structure"))[:6])
    risk = "\n".join(f"- {clean(x)}" for x in safe_list(persona_context.get("risk_phrasing"))[:5])

    callback_rows = []
    for row in safe_list(memory_context.get("callback_candidates"))[:3]:
        row = safe_dict(row)
        callback_rows.append(
            f"- thread={clean(row.get('thread_id'))} headline={clean(row.get('headline'))} summary={clean(row.get('last_summary'))}"
        )

    return f"""
You are {clean(persona_context.get("display_name")).upper()} on ToknNews.

YOUR JOB
--------
Generate one final spoken line for a collaborative anchor round.
This is a real broadcast prep discussion, not a summary generator.

CURRENT ROLE
------------
role: {clean(role_spec.get("role"))}
stance: {clean(role_spec.get("stance"))}
instruction: {clean(role_spec.get("instruction"))}

PERSONA
-------
role: {clean(persona_context.get("role"))}
domains: {json.dumps(safe_list(persona_context.get("domains")))}
voice_id: {clean(persona_context.get("voice_id"))}

persona lines:
{persona_lines or "- none"}

preferred phrasing:
{phrasing or "- none"}

preferred structures:
{structures or "- none"}

risk phrasing:
{risk or "- none"}

gpt rules:
{json.dumps(safe_dict(persona_context.get("gpt_rules")))}

lexicon:
{json.dumps(safe_dict(persona_context.get("lexicon")))}

cadence:
{json.dumps(safe_dict(persona_context.get("cadence")))}

latenight:
{json.dumps(safe_dict(persona_context.get("latenight")))}

MEMORY
------
anchor history:
{json.dumps(safe_dict(memory_context.get("anchor_history")))}

domain heat:
{json.dumps(safe_dict(memory_context.get("domain_heat")))}

callback candidates:
{chr(10).join(callback_rows) if callback_rows else "- none"}

SEGMENT CONTEXT
---------------
{json.dumps(shared_story_context, indent=2)}

HARD RULES
----------
- Never repeat the ingest summary verbatim unless a number or exact fact matters
- Sound like this anchor, not a generic analyst
- Add insight, tension, support, disagreement, or synthesis
- One or two sentences maximum
- No filler endings like "what matters next" or "the focal entity is"
- No fake certainty
- If you reference a number, use it naturally
- If you disagree, do it constructively
- If you are Chip, sound like a host with real judgment
- If you are Bitsy, stay under 16 words and stay meta
- Output plain spoken text only

RETURN
------
Return only the final spoken line.
""".strip()


# ---------------------------------------------------------
# BACKEND ADAPTERS
# ---------------------------------------------------------

def run_openclaw_agent(agent_name: str, payload: Dict[str, Any]) -> Tuple[bool, str, str]:
    """
    OpenClaw adapter.
    Because exact CLI invocation may vary by your setup, this uses a required
    command template environment variable instead of guessing.
    """
    if GLOBAL_FALLBACK_MODE:
        return False, "", "global_fallback_mode"

    if not OPENCLAW_ENABLED:
        return False, "", "openclaw_not_found"

    if not OPENCLAW_COMMAND_TEMPLATE:
        return False, "", "missing_TOKN_OPENCLAW_COMMAND_TEMPLATE"

    tmp_dir = Path("/tmp/toknnews_openclaw")
    tmp_dir.mkdir(parents=True, exist_ok=True)

    input_path = tmp_dir / f"{agent_name}_{int(time.time() * 1000)}.json"
    input_path.write_text(json.dumps(payload, indent=2))

    command = OPENCLAW_COMMAND_TEMPLATE.format(
        agent=agent_name,
        input_file=str(input_path),
    )

    try:
        completed = subprocess.run(
            ["bash", "-lc", command],
            capture_output=True,
            text=True,
            timeout=120,
        )

        stdout = clean(completed.stdout)
        stderr = clean(completed.stderr)

        if completed.returncode != 0:
            return False, "", f"openclaw_command_failed::{stderr or stdout}"

        # Prefer JSON with {"text": "..."} but accept plain text output
        text = stdout
        try:
            parsed = json.loads(stdout)
            if isinstance(parsed, dict):
                text = clean(parsed.get("text") or parsed.get("output") or parsed.get("content"))
        except Exception:
            pass

        return True, sanitize_tts(text), ""

    except Exception as e:
        return False, "", f"openclaw_exception::{clean(e)}"


def run_openai_agent(prompt: str) -> Tuple[bool, str, str]:
    if GLOBAL_FALLBACK_MODE:
        return False, "", "global_fallback_mode"

    if not OPENAI_ENABLED or openai is None:
        return False, "", "openai_unavailable"

    try:
        response = openai.ChatCompletion.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=OPENAI_TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS,
            request_timeout=30,
        )
        text = clean(response["choices"][0]["message"]["content"])
        return True, sanitize_tts(text), ""
    except Exception as e:
        return False, "", f"openai_exception::{clean(e)}"


def deterministic_fallback_line(
    speaker: str,
    role_spec: Dict[str, str],
    shared_story_context: Dict[str, Any],
) -> str:
    speaker = clean(speaker).lower()
    domain = clean(shared_story_context.get("domain")).lower()
    thesis = clean(shared_story_context.get("thesis"))
    implication = clean(shared_story_context.get("implication"))
    signal_type = clean(shared_story_context.get("signal_type"))
    entities = [clean(x) for x in safe_list(shared_story_context.get("entities")) if clean(x)]

    if speaker == "chip":
        if role_spec.get("role") == "host_open":
            return sanitize_tts(
                f"The headline is {thesis}, but the real issue is whether the underlying setup actually supports it."
            )
        if role_spec.get("role") == "host_challenge":
            return sanitize_tts(
                "That only matters if the follow-through confirms it instead of fading into narrative noise."
            )
        return sanitize_tts(
            "For viewers, the key is separating the signal from the reflexive reaction around it."
        )

    if speaker == "bond":
        return sanitize_tts(
            "Macro still sets the backdrop here, and the durability of this move depends on that backdrop cooperating."
        )

    if speaker == "reef":
        return sanitize_tts(
            "What matters is whether capital is actually concentrating here or just rotating through it briefly."
        )

    if speaker == "ledger":
        return sanitize_tts(
            "The transfer mechanics matter more than the headline because they tell you whether the flow is real."
        )

    if speaker == "lawson":
        return sanitize_tts(
            "The legal and policy angle matters because behavior usually changes before the narrative catches up."
        )

    if speaker == "cash":
        return sanitize_tts(
            "Trader behavior is the tell here, because price can move faster than conviction."
        )

    if speaker == "ivy":
        return sanitize_tts(
            "The crowd is reacting to the headline, but the real question is how long that emotional cycle lasts."
        )

    if speaker == "penny":
        return sanitize_tts(
            "In plain English, this matters because people will respond to it before they fully understand it."
        )

    if speaker == "bitsy":
        return "That is ridiculous even by crypto standards."

    entity_text = entities[0] if entities else "the market"
    return sanitize_tts(
        f"The implication for {entity_text} depends on whether {signal_type or implication or thesis} holds up."
    )


def generate_agent_line(
    speaker: str,
    role_spec: Dict[str, str],
    persona_context: Dict[str, Any],
    memory_context: Dict[str, Any],
    shared_story_context: Dict[str, Any],
) -> Dict[str, Any]:
    prompt = build_agent_prompt(
        speaker=speaker,
        role_spec=role_spec,
        persona_context=persona_context,
        memory_context=memory_context,
        shared_story_context=shared_story_context,
    )

    payload = {
        "speaker": speaker,
        "role_spec": role_spec,
        "persona_context": persona_context,
        "memory_context": memory_context,
        "shared_story_context": shared_story_context,
        "prompt": prompt,
    }

    backend_used = "fallback"
    ok = False
    text = ""
    error = ""

    if AGENT_BACKEND == "openclaw":
        ok, text, error = run_openclaw_agent(speaker, payload)
        backend_used = "openclaw" if ok else "fallback"

        if (not ok) and OPENAI_ENABLED:
            ok, text, error = run_openai_agent(prompt)
            backend_used = "openai" if ok else "fallback"

    elif AGENT_BACKEND == "openai":
        ok, text, error = run_openai_agent(prompt)
        backend_used = "openai" if ok else "fallback"

    if not ok or not text:
        text = deterministic_fallback_line(
            speaker=speaker,
            role_spec=role_spec,
            shared_story_context=shared_story_context,
        )
        backend_used = "fallback"

    return {
        "speaker": clean(speaker).lower(),
        "text": sanitize_tts(text),
        "backend": backend_used,
        "error": clean(error),
        "voice_id": clean(persona_context.get("voice_id")),
        "display_name": clean(persona_context.get("display_name")),
        "role": clean(role_spec.get("role")),
        "stance": clean(role_spec.get("stance")),
    }


# ---------------------------------------------------------
# ROUND ENGINE
# ---------------------------------------------------------

def build_block_priority(block: Dict[str, Any]) -> float:
    heat = safe_float(block.get("heat"), 0.0)
    context = safe_dict(block.get("context"))
    confidence = safe_float(context.get("confidence"), 0.0)
    pd_hints = safe_dict(block.get("pd_hints"))
    debate_bonus = 2.0 if bool(pd_hints.get("debate_potential")) else 0.0
    numeric_bonus = 1.0 if bool(pd_hints.get("requires_numeric")) else 0.0
    return round(heat + confidence + debate_bonus + numeric_bonus, 4)


def select_blocks_for_round(dialogue_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blocks = [safe_dict(x) for x in dialogue_blocks if isinstance(x, dict)]
    blocks.sort(key=build_block_priority, reverse=True)
    return blocks[:max(1, MAX_BLOCKS)]


def run_round_for_block(
    block: Dict[str, Any],
    episode_context: Dict[str, Any],
) -> Dict[str, Any]:
    domain = normalize_domain(clean(block.get("domain")))
    panel = build_anchor_panel(block)
    turn_order = choose_turn_order(panel, domain)
    source_digest = build_source_digest(block)
    shared_notes: List[Dict[str, Any]] = []
    turns: List[Dict[str, Any]] = []

    for idx, speaker in enumerate(turn_order):
        role_spec = build_role_instruction(
            speaker=speaker,
            turn_index=idx,
            total_turns=len(turn_order),
            panel=panel,
            block=block,
        )

        persona_context = build_persona_prompt_context(speaker)
        memory_context = build_memory_context(
            speaker=speaker,
            domain=domain,
            thread_id=clean(safe_dict(block.get("pd_hints")).get("thread_id")),
        )
        shared_story_context = build_shared_story_context(
            block=block,
            episode_context=episode_context,
            source_digest=source_digest,
            shared_notes=shared_notes,
        )

        generated = generate_agent_line(
            speaker=speaker,
            role_spec=role_spec,
            persona_context=persona_context,
            memory_context=memory_context,
            shared_story_context=shared_story_context,
        )

        turn_row = {
            "speaker": generated["speaker"],
            "text": generated["text"],
            "backend": generated["backend"],
            "role": generated["role"],
            "stance": generated["stance"],
            "voice_id": generated["voice_id"],
            "display_name": generated["display_name"],
        }
        turns.append(turn_row)

        shared_notes.append(
            {
                "speaker": generated["speaker"],
                "role": generated["role"],
                "stance": generated["stance"],
                "text": generated["text"],
            }
        )

    discussion_summary = summarize_round(block, turns)

    return {
        "narrative_id": clean(block.get("narrative_id")),
        "domain": domain,
        "panel": panel,
        "turn_order": turn_order,
        "source_digest": source_digest,
        "turns": turns,
        "discussion_summary": discussion_summary,
        "generated_at": _now_ts(),
    }


def summarize_round(block: Dict[str, Any], turns: List[Dict[str, Any]]) -> Dict[str, Any]:
    chip_lines = [clean(x.get("text")) for x in turns if clean(x.get("speaker")) == "chip"]
    analyst_lines = [clean(x.get("text")) for x in turns if clean(x.get("speaker")) != "chip"]
    domain = normalize_domain(clean(block.get("domain")))
    entities = [clean(x) for x in safe_list(block.get("entities")) if clean(x)]

    return {
        "headline": clean(block.get("thesis")),
        "core_tension": chip_lines[0] if chip_lines else clean(block.get("implication")),
        "best_take": analyst_lines[0] if analyst_lines else clean(block.get("implication")),
        "close_take": analyst_lines[-1] if analyst_lines else clean(block.get("thesis")),
        "domain": domain,
        "entities": entities[:4],
    }


# ---------------------------------------------------------
# DIALOGUE BLOCK ENRICHMENT
# ---------------------------------------------------------

def build_enriched_dialogue_blocks(
    original_blocks: List[Dict[str, Any]],
    rounds: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    rounds_by_id = {
        clean(row.get("narrative_id")): safe_dict(row)
        for row in rounds
        if clean(safe_dict(row).get("narrative_id"))
    }

    out: List[Dict[str, Any]] = []

    for block in original_blocks:
        row = deepcopy(safe_dict(block))
        narrative_id = clean(row.get("narrative_id"))
        round_row = rounds_by_id.get(narrative_id)

        if not round_row:
            out.append(row)
            continue

        agent_turns = []
        panel = [clean(x).lower() for x in safe_list(round_row.get("panel")) if clean(x)]

        for turn in safe_list(round_row.get("turns")):
            turn = safe_dict(turn)
            agent_turns.append(
                {
                    "speaker": clean(turn.get("speaker")).lower(),
                    "text": sanitize_tts(clean(turn.get("text"))),
                }
            )

        row["source_dialogue"] = deepcopy(safe_list(row.get("dialogue")))
        row["dialogue"] = agent_turns
        row["anchors"] = panel
        row["agent_round"] = {
            "panel": panel,
            "turn_order": safe_list(round_row.get("turn_order")),
            "discussion_summary": safe_dict(round_row.get("discussion_summary")),
            "source_digest": safe_dict(round_row.get("source_digest")),
            "generated_at": round_row.get("generated_at"),
        }

        showrunner_interventions = safe_list(row.get("showrunner_interventions"))
        if len(agent_turns) >= 4:
            showrunner_interventions.append({"type": "wrap"})
        row["showrunner_interventions"] = unique_preserve(showrunner_interventions)

        out.append(row)

    return out


# ---------------------------------------------------------
# SHOW PREP OUTPUT
# ---------------------------------------------------------

def build_show_prep(
    rounds: List[Dict[str, Any]],
    episode_context: Dict[str, Any],
) -> Dict[str, Any]:
    lead_rounds = rounds[:3]
    prep_rows = []

    for row in lead_rounds:
        row = safe_dict(row)
        summary = safe_dict(row.get("discussion_summary"))
        prep_rows.append(
            {
                "narrative_id": clean(row.get("narrative_id")),
                "headline": clean(summary.get("headline")),
                "core_tension": clean(summary.get("core_tension")),
                "best_take": clean(summary.get("best_take")),
                "close_take": clean(summary.get("close_take")),
                "panel": safe_list(row.get("panel")),
                "domain": clean(row.get("domain")),
            }
        )

    return {
        "episode_thesis": clean(episode_context.get("episode_thesis")),
        "signal_summary": clean(episode_context.get("signal_summary")),
        "risk_direction": clean(episode_context.get("risk_direction")),
        "dominant_assets": safe_list(episode_context.get("dominant_assets")),
        "prep_segments": prep_rows,
        "generated_at": _now_ts(),
        "backend": AGENT_BACKEND,
        "late_night_mode": LATE_NIGHT_MODE,
    }


# ---------------------------------------------------------
# MEMORY UPDATES
# ---------------------------------------------------------

def update_memory_from_rounds(
    rounds: List[Dict[str, Any]],
    episode_context: Dict[str, Any],
) -> None:
    for row in rounds:
        row = safe_dict(row)
        summary = safe_dict(row.get("discussion_summary"))
        turns = safe_list(row.get("turns"))
        panel = [clean(x).lower() for x in safe_list(row.get("panel")) if clean(x)]

        update_memory_with_story(
            {
                "headline": clean(summary.get("headline")),
                "domain": clean(row.get("domain")),
                "summary": clean(summary.get("core_tension")) or clean(summary.get("best_take")),
                "thread_id": clean(row.get("narrative_id")),
                "entity": clean((safe_list(summary.get("entities")) or [""])[0]),
                "signal_type": clean(row.get("domain")),
                "anchors": panel,
            }
        )

        for turn in turns:
            turn = safe_dict(turn)
            speaker = clean(turn.get("speaker")).lower()
            if speaker and speaker not in panel:
                panel.append(speaker)

    update_memory_with_episode(
        {
            "episode_id": f"episode_{int(time.time())}",
            "episode_thesis": clean(episode_context.get("episode_thesis")),
            "domains": unique_preserve([clean(safe_dict(x).get("domain")) for x in rounds if clean(safe_dict(x).get("domain"))]),
            "anchors": unique_preserve(
                [
                    clean(anchor).lower()
                    for row in rounds
                    for anchor in safe_list(safe_dict(row).get("panel"))
                    if clean(anchor)
                ]
            ),
            "callback_threads": [
                clean(safe_dict(x).get("narrative_id"))
                for x in rounds
                if clean(safe_dict(x).get("narrative_id"))
            ][:12],
        }
    )


# ---------------------------------------------------------
# MAIN
# ---------------------------------------------------------

def run() -> None:
    dialogue_blocks = load_json(INPUT_DIALOGUE_BLOCKS, [])
    episode_context = load_json(INPUT_EPISODE_CONTEXT, {})

    if not isinstance(dialogue_blocks, list) or not dialogue_blocks:
        raise FileNotFoundError("Missing or empty dialogue_blocks.json")

    if not isinstance(episode_context, dict):
        episode_context = {}

    selected_blocks = select_blocks_for_round(dialogue_blocks)

    _emit_openclaw_event(
        "anchor_round_start",
        {
            "selected_blocks": len(selected_blocks),
            "backend": AGENT_BACKEND,
            "openclaw_enabled": OPENCLAW_ENABLED,
            "global_fallback_mode": GLOBAL_FALLBACK_MODE,
        },
    )

    rounds: List[Dict[str, Any]] = []

    for block in selected_blocks:
        narrative_id = clean(safe_dict(block).get("narrative_id"))
        domain = clean(safe_dict(block).get("domain"))

        _emit_openclaw_event(
            "anchor_round_segment_start",
            {
                "narrative_id": narrative_id,
                "domain": domain,
            },
        )

        round_row = run_round_for_block(block, episode_context)
        rounds.append(round_row)

        _emit_openclaw_event(
            "anchor_round_segment_complete",
            {
                "narrative_id": narrative_id,
                "panel": safe_list(round_row.get("panel")),
            },
        )

    enriched_dialogue = build_enriched_dialogue_blocks(dialogue_blocks, rounds)
    show_prep = build_show_prep(rounds, episode_context)

    update_memory_from_rounds(rounds, episode_context)

    atomic_write_json(OUTPUT_ROUNDS, TMP_ROUNDS, rounds)
    atomic_write_json(OUTPUT_AGENT_DIALOGUE, TMP_AGENT_DIALOGUE, enriched_dialogue)
    atomic_write_json(OUTPUT_SHOW_PREP, TMP_SHOW_PREP, show_prep)

    _emit_openclaw_event(
        "anchor_round_complete",
        {
            "rounds": len(rounds),
            "output_rounds": str(OUTPUT_ROUNDS),
            "output_dialogue": str(OUTPUT_AGENT_DIALOGUE),
        },
    )

    print(f"[ANCHOR ROUND] blocks_selected={len(selected_blocks)}")
    print(f"[ANCHOR ROUND] rounds_written={OUTPUT_ROUNDS}")
    print(f"[ANCHOR ROUND] dialogue_written={OUTPUT_AGENT_DIALOGUE}")
    print(f"[ANCHOR ROUND] show_prep_written={OUTPUT_SHOW_PREP}")
    print(f"[ANCHOR ROUND] backend={AGENT_BACKEND}")
    print(f"[ANCHOR ROUND] openclaw_enabled={OPENCLAW_ENABLED}")
    print(f"[ANCHOR ROUND] global_fallback_mode={GLOBAL_FALLBACK_MODE}")


if __name__ == "__main__":
    run()
