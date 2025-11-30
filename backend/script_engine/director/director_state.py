#!/usr/bin/env python3
"""
TOKNNews — Director State (Persistent PD + Character Memory)
Module C-7
"""

import os, json, time

STATE_PATH = "/var/www/toknnews-live/backend/script_engine/director/director_state.json"

DEFAULT_STATE = {
    "intro_played": False,
    "last_segment_type": None,
    "last_anchor_used": None,
    "vega_last_used": 0,
    "bitsy_last_used": 0,
    "cycle_index": 0,
    "chip_memory": {
        "last_theme": None,
        "last_risk": None,
        "last_toss_target": None
    },
    "anchor_memory": {
        "reef": {"last_used": 0},
        "lawson": {"last_used": 0},
        "bond": {"last_used": 0},
        "ivy": {"last_used": 0},
        "cash": {"last_used": 0},
        "ledger": {"last_used": 0}
    }
}


def load_state():
    if not os.path.exists(STATE_PATH):
        return DEFAULT_STATE.copy()
    try:
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    except:
        return DEFAULT_STATE.copy()


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)
