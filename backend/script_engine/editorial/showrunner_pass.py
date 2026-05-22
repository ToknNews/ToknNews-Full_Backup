#!/usr/bin/env python3
"""
showrunner_pass.py

ToknNews — Episode-Level Showrunner Pass

Purpose:
- Enforce episode-level broadcast structure
- Add Chip intervention metadata across the full episode
- Protect runtime, transitions, numeric coverage, culture lane, and narrative continuity
- DOES NOT generate dialogue
- DOES NOT modify dialogue text
- Outputs structured showrunner intervention metadata
"""

import json
import os
import re
import openai
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv("/opt/toknnews/.env")
openai.api_key = os.getenv("OPENAI_API_KEY")

MODEL = os.getenv("TOKN_SHOWRUNNER_MODEL", "gpt-4.1-mini")

TARGET_RUNTIME_SEC = int(os.getenv("TOKN_TARGET_RUNTIME_SEC", "600"))
MIN_RUNTIME_SEC = int(os.getenv("TOKN_MIN_RUNTIME_SEC", "520"))
MAX_RUNTIME_SEC = int(os.getenv("TOKN_MAX_RUNTIME_SEC", "680"))

HIGH_HEAT_THRESHOLD = float(os.getenv("TOKN_SHOWRUNNER_HIGH_HEAT", "7.0"))

NUMERIC_RE = re.compile(
    r"(\$?\d[\d,]*(?:\.\d+)?(?:\s?(?:%|k|K|m|M|b|B|million|billion))?)"
)

ANCHOR_ROLE_HINTS = {
    "chip": "strategist",
    "bond": "macro",
    "cash": "markets",
    "lawson": "regulation",
    "ledger": "onchain",
    "reef": "defi",
    "neura": "ai",
    "bitsy": "culture",
    "penny": "retail",
    "rex": "general",
}

DOMAIN_TRANSITION_TONES = {
    ("markets", "onchain"): "hard_shift",
    ("onchain", "macro"): "zoom_out",
    ("macro", "regulation"): "soft_pivot",
    ("regulation", "defi"): "soft_pivot",
    ("defi", "ai"): "soft_pivot",
    ("ai", "culture"): "soft_pivot",
    ("markets", "culture"): "callback",
    ("onchain", "culture"): "callback",
    ("culture", "general"): "wrap",
}


# --------------------------------------------------
# Utilities
# --------------------------------------------------

def _safe_str(x: Any) -> str:
    return "" if x is None else str(x).strip()


def _has_numeric_reference(text: str) -> bool:
    if not isinstance(text, str):
        return False
    return bool(NUMERIC_RE.search(text))


def _dialogue_has_numeric(dialogue: List[Dict[str, str]]) -> bool:
    for turn in dialogue:
        if _has_numeric_reference(turn.get("text", "")):
            return True
    return False


def _block_has_numeric_hook(block: Dict[str, Any]) -> bool:
    pd_hints = block.get("pd_hints", {}) or {}
    numeric_hook = pd_hints.get("numeric_hook")
    if numeric_hook and _safe_str(numeric_hook):
        return True

    numeric_context = pd_hints.get("numeric_context")
    if isinstance(numeric_context, dict) and numeric_context:
        return True

    signal_context = pd_hints.get("signal_context")
    if isinstance(signal_context, list) and signal_context:
        return True

    return False


def _contains_explicit_challenge(dialogue: List[Dict[str, str]]) -> bool:
    challenge_markers = [
        "that assumes",
        "i disagree",
        "but that ignores",
        "wait",
        "hold on",
        "not necessarily",
        "i'm not convinced",
        "that doesn't follow",
    ]
    blob = " ".join(_safe_str(t.get("text")).lower() for t in dialogue)
    return any(marker in blob for marker in challenge_markers)


def _too_dense(dialogue: List[Dict[str, str]]) -> bool:
    long_turns_in_row = 0
    for turn in dialogue:
        text = _safe_str(turn.get("text"))
        word_count = len(text.split())
        if word_count >= 24:
            long_turns_in_row += 1
            if long_turns_in_row >= 3:
                return True
        else:
            long_turns_in_row = 0
    return False


def _estimate_episode_runtime(dialogue_blocks: List[Dict[str, Any]]) -> int:
    total = 0
    for block in dialogue_blocks:
        total += int(block.get("recommended_runtime_sec") or 0)
    return total


def _get_domain(block: Dict[str, Any]) -> str:
    return _safe_str(block.get("domain", "general")).lower()


def _get_thread_id(block: Dict[str, Any]) -> str:
    pd_hints = block.get("pd_hints", {}) or {}
    return _safe_str(pd_hints.get("thread_id"))


def _get_heat(block: Dict[str, Any]) -> float:
    try:
        return float(block.get("heat", 5.0))
    except Exception:
        return 5.0


def _get_anchors(block: Dict[str, Any]) -> List[str]:
    anchors = block.get("anchors") or []
    return [str(a).lower() for a in anchors if a]


def _domain_transition_tone(prev_domain: str, cur_domain: str) -> str:
    return DOMAIN_TRANSITION_TONES.get((prev_domain, cur_domain), "soft_pivot")


def _culture_present(dialogue_blocks: List[Dict[str, Any]]) -> bool:
    for block in dialogue_blocks:
        domain = _get_domain(block)
        if domain in {"culture", "sentiment", "retail"}:
            return True
        text_blob = " ".join(
            _safe_str(turn.get("text")).lower()
            for turn in block.get("dialogue", [])
        )
        if any(k in text_blob for k in ["meme", "memecoin", "reddit", "x ", "twitter", "retail"]):
            return True
    return False


def _looks_like_role_mismatch(block: Dict[str, Any]) -> bool:
    """
    Only flag true mismatches.
    Accept strong adjacent-role combinations.
    """
    domain = _get_domain(block)
    anchors = _get_anchors(block)

    if not anchors:
        return False

    primary = anchors[0]
    secondary = anchors[1] if len(anchors) > 1 else None

    acceptable = {
        "markets": {"cash", "bond", "chip"},
        "macro": {"bond", "chip", "lawson"},
        "regulation": {"lawson", "bond", "chip"},
        "onchain": {"ledger", "reef", "chip"},
        "defi": {"reef", "ledger", "chip"},
        "ai": {"neura", "chip"},
        "culture": {"bitsy", "penny", "chip"},
        "retail": {"bitsy", "penny", "chip"},
        "general": {"chip", "bond", "cash", "ledger", "reef", "neura", "bitsy", "penny", "lawson", "rex"},
    }

    allowed = acceptable.get(domain, acceptable["general"])

    if primary in allowed:
        return False

    if secondary and secondary in allowed:
        return False

    return True


def _detect_repetitive_structure(blocks: List[Dict[str, Any]]) -> List[int]:
    """
    Detect repeated A-B-A style structures across consecutive segments.
    Returns block indices that should vary.
    """
    flagged = []

    def signature(block: Dict[str, Any]) -> str:
        dialogue = block.get("dialogue", []) or []
        speakers = [_safe_str(t.get("speaker")).lower() for t in dialogue]
        return "-".join(speakers[:3])

    if len(blocks) < 3:
        return flagged

    sigs = [signature(b) for b in blocks]

    for i in range(2, len(sigs)):
        if sigs[i] and sigs[i] == sigs[i - 1] == sigs[i - 2]:
            flagged.append(i)

    return flagged


# --------------------------------------------------
# GPT: Detect ambiguous internal topic shifts only
# --------------------------------------------------

def analyze_topic_shifts(dialogue: List[Dict[str, str]]) -> List[int]:
    if len(dialogue) < 5:
        return []

    numbered = "\n".join(
        f"{i}. {t.get('speaker', '').upper()}: {t.get('text', '')}"
        for i, t in enumerate(dialogue)
    )

    prompt = f"""
You are a broadcast showrunner.

Identify ONLY meaningful INTERNAL topic shifts inside this single segment dialogue where
the host should re-frame context for the audience.

Rules:
- Ignore speaker changes
- Ignore normal disagreement
- Ignore short clarifications
- Flag only REAL internal asset / narrative / domain shifts

Return JSON ONLY:
{{
  "break_after_turns": [integer indices]
}}

Indices are ZERO-BASED.

Conversation:
{numbered}
""".strip()

    try:
        rsp = openai.ChatCompletion.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=120,
            request_timeout=10,
        )

        raw = rsp["choices"][0]["message"]["content"].strip()

        if not raw.startswith("{"):
            return []

        data = json.loads(raw)
        breaks = data.get("break_after_turns", [])

        return [int(i) for i in breaks if isinstance(i, int)]

    except Exception as e:
        print("[SHOWRUNNER][GPT_TOPIC_SHIFT_ERROR]", e)
        return []


# --------------------------------------------------
# Episode-level intervention planning
# --------------------------------------------------

def _episode_level_interventions(dialogue_blocks: List[Dict[str, Any]]) -> Dict[int, List[Dict[str, Any]]]:
    by_block: Dict[int, List[Dict[str, Any]]] = {i: [] for i in range(len(dialogue_blocks))}

    if not dialogue_blocks:
        return by_block

    # Cold open protection
    first_block = dialogue_blocks[0]
    first_dialogue = first_block.get("dialogue", []) or []
    if first_dialogue and _safe_str(first_dialogue[0].get("speaker")).lower() != "chip":
        by_block[0].append({
            "index": -1,
            "type": "cold_open",
            "tone": "hard_shift",
            "reason": "Episode should open with Chip framing the audience entry point."
        })

    # Culture cannot open the show
    first_domain = _get_domain(dialogue_blocks[0])
    if first_domain in {"culture", "sentiment", "retail"}:
        by_block[0].append({
            "index": -1,
            "type": "segment_reorder",
            "tone": "hard_shift",
            "reason": f"Episode opens with {first_domain}; culture should not lead the show."
        })

    # Runtime governance
    est_runtime = _estimate_episode_runtime(dialogue_blocks)

    if est_runtime < MIN_RUNTIME_SEC:
        by_block[len(dialogue_blocks) - 1].append({
            "index": -1,
            "type": "runtime_extend",
            "tone": "soft_pivot",
            "reason": f"Estimated runtime {est_runtime}s is below minimum {MIN_RUNTIME_SEC}s."
        })

    if est_runtime > MAX_RUNTIME_SEC:
        by_block[len(dialogue_blocks) - 1].append({
            "index": -1,
            "type": "runtime_trim",
            "tone": "hard_shift",
            "reason": f"Estimated runtime {est_runtime}s exceeds maximum {MAX_RUNTIME_SEC}s."
        })

    # If show is short and has many blocks, suggest merge candidates
    if est_runtime < MIN_RUNTIME_SEC and len(dialogue_blocks) >= 8:
        for idx in range(1, len(dialogue_blocks) - 1, 2):
            by_block[idx].append({
                "index": -1,
                "type": "segment_merge_candidate",
                "tone": "soft_pivot",
                "reason": "Show is short and fragmented; adjacent segments may be better merged."
            })

    # Segment-level deterministic transitions + thread callbacks
    prev_domain = None
    prev_thread = None
    thread_missing_count = 0

    for i, block in enumerate(dialogue_blocks):
        cur_domain = _get_domain(block)
        cur_thread = _get_thread_id(block)

        if not cur_thread:
            thread_missing_count += 1

        if i > 0:
            if prev_domain != cur_domain:
                by_block[i].append({
                    "index": -1,
                    "type": "transition",
                    "tone": _domain_transition_tone(prev_domain, cur_domain),
                    "reason": f"Domain shift from {prev_domain} to {cur_domain}."
                })

            if prev_thread and cur_thread and prev_thread == cur_thread:
                by_block[i].append({
                    "index": -1,
                    "type": "thread_callback",
                    "tone": "callback",
                    "reason": f"Thread continuity detected: {cur_thread}."
                })

        prev_domain = cur_domain
        prev_thread = cur_thread

    # Thread propagation quality
    if len(dialogue_blocks) > 0 and thread_missing_count > (len(dialogue_blocks) / 2):
        by_block[len(dialogue_blocks) - 1].append({
            "index": -1,
            "type": "thread_missing",
            "tone": "soft_pivot",
            "reason": f"Thread IDs missing in {thread_missing_count} of {len(dialogue_blocks)} blocks."
        })

    # Culture lane enforcement
    if not _culture_present(dialogue_blocks):
        last_idx = min(len(dialogue_blocks) - 1, 4) if len(dialogue_blocks) > 1 else 0
        by_block[last_idx].append({
            "index": -1,
            "type": "culture_injection",
            "tone": "soft_pivot",
            "reason": "Episode lacks explicit culture / retail / meme / Reddit / X pulse."
        })

    # Repetitive structure detection across segments
    repetitive_idxs = _detect_repetitive_structure(dialogue_blocks)
    for idx in repetitive_idxs:
        by_block[idx].append({
            "index": -1,
            "type": "structure_variation",
            "tone": "soft_pivot",
            "reason": "Repeated dialogue structure detected across consecutive segments."
        })

    return by_block


# --------------------------------------------------
# Block-level intervention planning
# --------------------------------------------------

def _block_level_interventions(block: Dict[str, Any]) -> List[Dict[str, Any]]:
    interventions: List[Dict[str, Any]] = []

    dialogue = block.get("dialogue", []) or []
    heat = _get_heat(block)

    if not dialogue:
        return interventions

    # Internal topic shifts only if ambiguous / long enough
    topic_breaks = analyze_topic_shifts(dialogue)
    for idx in topic_breaks:
        interventions.append({
            "index": idx,
            "type": "transition",
            "tone": "soft_pivot",
            "reason": "Internal narrative shift detected inside segment."
        })

    # Numeric coverage validation
    if not _dialogue_has_numeric(dialogue) and not _block_has_numeric_hook(block):
        interventions.append({
            "index": max(0, min(1, len(dialogue) - 1)),
            "type": "numeric_probe",
            "tone": "hard_shift",
            "reason": "Segment lacks a numeric anchor despite available context."
        })

    # Debate escalation
    if heat >= HIGH_HEAT_THRESHOLD and not _contains_explicit_challenge(dialogue):
        interventions.append({
            "index": max(1, len(dialogue) // 2),
            "type": "debate_escalation",
            "tone": "hard_shift",
            "reason": f"Heat {heat} is high but challenge/friction is too weak."
        })

    # Pace reset
    if _too_dense(dialogue):
        interventions.append({
            "index": max(1, len(dialogue) // 2),
            "type": "pace_reset",
            "tone": "zoom_out",
            "reason": "Three or more dense turns in sequence detected."
        })

    # Anchor role enforcement
    if _looks_like_role_mismatch(block):
        interventions.append({
            "index": 0,
            "type": "anchor_reframe",
            "tone": "soft_pivot",
            "reason": "Primary anchor may not match the segment domain."
        })

    # Wrap protection
    if _safe_str(dialogue[-1].get("speaker")).lower() != "chip":
        interventions.append({
            "index": len(dialogue) - 1,
            "type": "wrap",
            "tone": "wrap",
            "reason": "Segment should close with Chip synthesis or handoff."
        })

    return interventions


# --------------------------------------------------
# Public API
# --------------------------------------------------

def run_showrunner_pass(dialogue_blocks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not isinstance(dialogue_blocks, list):
        return []

    for block in dialogue_blocks:
        if not isinstance(block, dict):
            continue
        block.setdefault("showrunner_interventions", [])

    episode_interventions = _episode_level_interventions(dialogue_blocks)

    for idx, block in enumerate(dialogue_blocks):
        dialogue = block.get("dialogue", [])

        if not isinstance(dialogue, list) or not dialogue:
            block["showrunner_interventions"] = []
            continue

        interventions = []

        # Episode-level
        interventions.extend(episode_interventions.get(idx, []))

        # Block-level
        interventions.extend(_block_level_interventions(block))

        # Deduplicate by (index, type)
        seen = set()
        clean = []
        for item in interventions:
            key = (item.get("index"), item.get("type"))
            if key not in seen:
                seen.add(key)
                clean.append(item)

        block["showrunner_interventions"] = sorted(
            clean,
            key=lambda x: (x.get("index", 0), x.get("type", ""))
        )

    # Episode metadata
    est_runtime = _estimate_episode_runtime(dialogue_blocks)
    culture_present = _culture_present(dialogue_blocks)

    for i, block in enumerate(dialogue_blocks):
        block["showrunner_meta"] = {
            "episode_estimated_runtime_sec": est_runtime,
            "episode_target_runtime_sec": TARGET_RUNTIME_SEC,
            "episode_min_runtime_sec": MIN_RUNTIME_SEC,
            "episode_max_runtime_sec": MAX_RUNTIME_SEC,
            "culture_present": culture_present,
            "block_index": i,
            "block_domain": _get_domain(block),
            "block_thread_id": _get_thread_id(block),
        }

    print(f"[SHOWRUNNER] runtime={est_runtime}s blocks={len(dialogue_blocks)} culture_present={culture_present}")

    return dialogue_blocks
