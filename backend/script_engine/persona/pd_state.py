#!/usr/bin/env python3
"""
pd_state.py
ToknNews V2 — PDv4 State Handler
Tracks usage of anchors for fatigue + rotation.
"""

import json
from pathlib import Path

STATE_PATH = Path("/opt/toknnews/data/pd_state.json")

DEFAULT_STATE = {
    "anchor_usage": {
        "chip": 0, "bond": 0, "cash": 0, "ledger": 0, "neura": 0,
        "reef": 0, "lawson": 0, "bitsy": 0, "penny": 0, "rex": 0
    },
    "last_anchors": [],
    "episode_count": 0
}

def load_pd_state():
    if STATE_PATH.exists():
        try:
            return json.loads(STATE_PATH.read_text())
        except:
            return DEFAULT_STATE.copy()
    return DEFAULT_STATE.copy()

def save_pd_state(state):
    STATE_PATH.write_text(json.dumps(state, indent=2))

def update_anchor_usage(state, anchors):
    for a in anchors:
        if a in state["anchor_usage"]:
            state["anchor_usage"][a] += 1
    return state
