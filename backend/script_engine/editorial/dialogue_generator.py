#!/usr/bin/env python3
"""
dialogue_generator.py
ToknNews — Dialogue Generator (v3.1 BROADCAST REALISM)

Enhancements:
- Heat-driven turn count
- Numeric context enforcement
- Anchor role normalization
- Structured debate cadence
- Phrase suppression
"""

import os
import json
import time
import signal
from typing import Any, Dict, List
from dotenv import load_dotenv
from backend.script_engine.editorial.showrunner_pass import run_showrunner_pass
from backend.script_engine.editorial.numeric_injector import build_numeric_context
import openai

INFILE = "/opt/toknnews/data/stories/narrative_briefs.json"
OUTFILE = "/opt/toknnews/data/stories/dialogue_blocks.json"
DOTENV = "/opt/toknnews/.env"

DEFAULT_MODEL = os.getenv("TOKN_DIALOGUE_MODEL", "gpt-4.1-mini")
DEFAULT_TIMEOUT_SEC = int(os.getenv("TOKN_DIALOGUE_TIMEOUT_SEC", "25"))
DEFAULT_MAX_RETRIES = int(os.getenv("TOKN_DIALOGUE_RETRIES", "2"))

FRICTION_HEAT_THRESHOLD = float(os.getenv("TOKN_FRICTION_HEAT", "6.0"))

SUPPRESSED_PHRASES = [
    "true, but",
    "risk skews toward",
    "unless",
    "that assumes"
]

# ------------------------------------------------------------
# Runtime → turn count policy
# ------------------------------------------------------------

def turns_for_runtime(runtime_sec: int, heat: float) -> int:

    if heat < 4:
        return 4
    elif heat < 6:
        return 5
    elif heat < 8:
        return 6
    else:
        return 7


# ------------------------------------------------------------
# Anchor normalization
# ------------------------------------------------------------

def normalize_anchors(domain: str, anchors: List[str]) -> List[str]:

    domain = (domain or "").lower()

    if domain == "markets":
        return ["cash", "bond"]

    if domain == "onchain":
        return ["ledger", "reef"]

    if domain == "macro":
        return ["bond", "chip"]

    if domain == "culture":
        return ["bitsy", "chip"]

    return anchors or ["chip"]


# ------------------------------------------------------------
# Utilities
# ------------------------------------------------------------

def _load_json(path: str) -> Any:
    with open(path, "r") as f:
        return json.load(f)


def _write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=2)


def _safe_str(x: Any) -> str:
    return "" if x is None else str(x).strip()


# ------------------------------------------------------------
# Phrase Suppression
# ------------------------------------------------------------

def _suppress_repetitive_phrasing(dialogue: List[Dict[str, str]]) -> List[Dict[str, str]]:
    used = set()

    for turn in dialogue:

        text_lower = turn["text"].lower()

        for phrase in SUPPRESSED_PHRASES:

            if phrase in text_lower:

                if phrase in used:
                    turn["text"] = turn["text"].replace(phrase, "")

                else:
                    used.add(phrase)

    return dialogue


# ------------------------------------------------------------
# Prompt Builder
# ------------------------------------------------------------

def _build_prompt(brief: Dict[str, Any], target_turns: int) -> str:

    domain = _safe_str(brief.get("domain", "general")).lower()

    anchors = normalize_anchors(
        domain,
        [a.lower() for a in (brief.get("anchors") or [])]
    )

    thesis = _safe_str(brief.get("thesis"))
    heat = float(brief.get("heat", 5.0))

    pd_hints = brief.get("pd_hints", {}) or {}

    chapter_summary = _safe_str(
        (pd_hints.get("chapter_context") or {}).get("summary")
    )

    grok_context = str(
        pd_hints.get("editorial_context")
        or pd_hints.get("context_injection")
        or ""
    )[:800]

    # --------------------------------------------------------
    # NUMERIC CONTEXT
    # --------------------------------------------------------

    numeric_points = build_numeric_context(brief)

    numeric_block = "\n".join(
        f"- {p.get('spoken')}"
        for p in numeric_points
        if p.get("spoken")
    ) or "None"

    numeric_required = "No"

    if numeric_points:
        numeric_required = "Yes"

    # --------------------------------------------------------
    # META CONTEXT
    # --------------------------------------------------------

    meta = brief.get("meta") or {}

    discussion_angle = _safe_str(meta.get("discussion_angle"))
    trend_context = _safe_str(meta.get("trend_context"))
    why_it_matters = _safe_str(meta.get("why_it_matters"))
    smart_money_view = _safe_str(meta.get("smart_money_view"))

    realism_layer = """
REALISM RULES:
- One line under 8 words
- One line under 18 words
- At least one direct question
- Vary sentence length
- Allow one blunt reaction
"""

    numeric_rules = f"""
NUMERIC CONTEXT:
{numeric_block}

NUMERIC REQUIREMENT: {numeric_required}

If numeric requirement is Yes:
- At least one line MUST include a number
"""

    friction_rule = ""

    if len(anchors) >= 2 and heat >= FRICTION_HEAT_THRESHOLD:

        friction_rule = """
DEBATE RULE:
Include at least one challenge:
- That assumes...
- I disagree because...
- But that ignores...
"""

    return f"""
Live ToknNews broadcast conversation.

DOMAIN: {domain.upper()}
ANCHORS: {", ".join(anchors).upper()}
LINES: exactly {target_turns}

Rules:
- No filler
- Do not repeat thesis wording
- Escalate logically
- JSON only list of objects {{speaker,text}}

CONVERSATION STRUCTURE:

Turn 1: frame situation
Turn 2: challenge
Turn 3: numeric evidence
Turn 4: interpretation
Turn 5+: synthesis

{realism_layer}

{numeric_rules}

{friction_rule}

CHAPTER CONTEXT:
{chapter_summary}

EDITORIAL META:
Discussion angle: {discussion_angle}
Trend context: {trend_context}
Why it matters: {why_it_matters}
Smart money view: {smart_money_view}

Signal Context:
{grok_context}

Return JSON ONLY.
""".strip()


# ------------------------------------------------------------
# GPT Call
# ------------------------------------------------------------

class GPTTimeout(Exception):
    pass


def _timeout_handler(signum, frame):
    raise GPTTimeout("Timeout")


def _call_gpt(prompt, model, timeout_sec, retries):

    last_err = None

    for attempt in range(1, retries + 2):

        try:

            signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(timeout_sec + 5)

            rsp = openai.ChatCompletion.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.55,
                max_tokens=750,
                request_timeout=timeout_sec,
            )

            signal.alarm(0)

            raw = rsp["choices"][0]["message"]["content"].strip()

            dialogue = json.loads(raw)

            return dialogue

        except Exception as e:

            last_err = e
            signal.alarm(0)
            time.sleep(0.5)

    raise RuntimeError(f"GPT failed: {last_err}")


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    load_dotenv(DOTENV)

    openai.api_key = os.getenv("OPENAI_API_KEY")

    briefs = _load_json(INFILE)

    out_blocks = []

    for brief in briefs:

        runtime_sec = int(brief.get("recommended_runtime_sec") or 35)

        heat = float(brief.get("heat", 5.0))

        target_turns = turns_for_runtime(runtime_sec, heat)

        prompt = _build_prompt(brief, target_turns)

        try:

            dialogue = _call_gpt(
                prompt,
                DEFAULT_MODEL,
                DEFAULT_TIMEOUT_SEC,
                DEFAULT_MAX_RETRIES
            )

        except Exception:

            anchors = normalize_anchors(
                brief.get("domain"),
                brief.get("anchors") or ["chip"]
            )

            dialogue = [
                {"speaker": anchors[0], "text": brief.get("thesis")},
                {"speaker": anchors[-1], "text": "But that assumes the move has real support."},
                {"speaker": anchors[0], "text": "That’s exactly the risk the market is trying to price."},
            ]

        dialogue = _suppress_repetitive_phrasing(dialogue)

        out_blocks.append({

            "narrative_id": brief.get("narrative_id"),
            "domain": brief.get("domain"),
            "anchors": normalize_anchors(
                brief.get("domain"),
                brief.get("anchors")
            ),
            "recommended_runtime_sec": runtime_sec,
            "turns": len(dialogue),
            "dialogue": dialogue,
            "ts": time.time(),
            "heat": heat,
            "pd_hints": brief.get("pd_hints", {}),

        })

    out_blocks = run_showrunner_pass(out_blocks)

    _write_json(OUTFILE, out_blocks)


if __name__ == "__main__":
    main()
