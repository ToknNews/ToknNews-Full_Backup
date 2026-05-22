#!/usr/bin/env python3
"""
████████╗ ██████╗ ██╗  ██╗███╗   ██╗
╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║
   ██║   ██║   ██║█████╔╝ ██╔██╗ ██║
   ██║   ██║   ██║██╔═██╗ ██║╚██╗██║
   ██║   ╚██████╔╝██║  ██╗██║ ╚████║
   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝

TOKNNEWS PERSONA ENGINE
Anchor Agent Runner (FAST CONVERSATION MODE)

Purpose
-------
Fast OpenClaw execution with:
• correct payload parsing
• conversational memory
• clean persona output
• minimal latency overhead
"""

from __future__ import annotations
import json, os, subprocess, time
from pathlib import Path
from typing import Any, Dict, List, Tuple

INPUT_PATH = Path("/opt/toknnews/data/stories/dialogue_blocks.json")
OUTPUT_PATH = Path("/opt/toknnews/data/stories/dialogue_blocks_executed.json")

TOKN_OPENCLAW_BIN = os.getenv("TOKN_OPENCLAW_BIN", "openclaw")
TOKN_OPENCLAW_AGENT_ID = os.getenv("TOKN_OPENCLAW_AGENT_ID", "main")
TOKN_OPENCLAW_TIMEOUT_SEC = int(os.getenv("TOKN_OPENCLAW_TIMEOUT_SEC", "20"))
TOKN_USE_OPENCLAW = os.getenv("TOKN_USE_OPENCLAW", "1") == "1"

MAX_BLOCKS = int(os.getenv("TOKN_MAX_BLOCKS", "5"))
MAX_TURNS = int(os.getenv("TOKN_MAX_TURNS", "3"))

# -------------------------
# HELPERS
# -------------------------
def now_ts():
    return time.time()

def clean(x):
    return "" if x is None else str(x).strip()

# -------------------------
# OPENCLAW (FIXED PARSER)
# -------------------------
def extract_text(payload: Dict[str, Any]) -> str:
    # correct OpenClaw shape
    for row in payload.get("payloads", []):
        if isinstance(row, dict) and row.get("text"):
            return row["text"]

    # fallback shapes
    if payload.get("response"):
        return payload["response"]

    if payload.get("text"):
        return payload["text"]

    return ""

def run_openclaw(message: str) -> Tuple[str, Dict[str, Any]]:
    if not TOKN_USE_OPENCLAW:
        return "", {"mode": "disabled"}

    cmd = [
        TOKN_OPENCLAW_BIN,
        "agent",
        "--agent", TOKN_OPENCLAW_AGENT_ID,
        "--message", message,
        "--local",
        "--json"
    ]

    try:
        rsp = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=TOKN_OPENCLAW_TIMEOUT_SEC,
        )
    except subprocess.TimeoutExpired:
        return "", {"mode": "timeout"}
    except Exception as e:
        return "", {"mode": "error", "reason": str(e)}

    if rsp.returncode != 0:
        return "", {"mode": "error", "stderr": rsp.stderr[:300]}

    try:
        payload = json.loads(rsp.stdout)
        text = extract_text(payload)
    except:
        text = rsp.stdout

    text = clean(text)

    if not text or text.startswith("You are"):
        return "", {"mode": "invalid_output"}

    return text, {"mode": "ok"}

# -------------------------
# PROMPT BUILDER (CRITICAL FIX)
# -------------------------
def build_prompt(anchor: str, line: str, history: List[Dict[str, str]]) -> str:
    last_turns = history[-2:]

    convo = "\n".join(
        f"{t['speaker']}: {t['text']}" for t in last_turns if t.get("text")
    ) or "No prior turns."

    return f"""
You are {anchor}, a panelist on a live financial roundtable.

Conversation so far:
{convo}

New signal:
{line}

Respond naturally.

Rules:
- Do not repeat the input
- Add insight or reaction
- Keep it short and spoken
""".strip()

# -------------------------
# FALLBACK (LAST RESORT ONLY)
# -------------------------
def fallback(anchor: str, line: str) -> str:
    return line  # no templated garbage

# -------------------------
# EXECUTION
# -------------------------
def execute_block(block: Dict[str, Any]) -> Dict[str, Any]:
    turns = block.get("dialogue", [])[:MAX_TURNS]
    executed = []

    for t in turns:
        line = clean(t.get("text"))
        anchor = clean(t.get("speaker")) or "bond"

        prompt = build_prompt(anchor, line, executed)

        text, meta = run_openclaw(prompt)

        if not text:
            text = fallback(anchor, line)

        executed.append({
            "speaker": anchor,
            "text": text
        })

    block["dialogue"] = executed
    block["execution_meta"] = {
        "time": now_ts()
    }

    return block

# -------------------------
# MAIN
# -------------------------
def main():
    data = json.loads(INPUT_PATH.read_text())
    data = data[:MAX_BLOCKS]

    out = []
    for block in data:
        out.append(execute_block(block))

    OUTPUT_PATH.write_text(json.dumps(out, indent=2))

    print(f"[ANCHOR RUNNER] DONE blocks={len(out)}")

if __name__ == "__main__":
    main()
