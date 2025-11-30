#!/usr/bin/env python3

import json
import os
import time

STATE_FILE = "/var/www/toknnews/data/director_state.json"

class DirectorState:
    """
    Lightweight PD memory — tracks:
        • last anchors used
        • last tone
        • last hijinx
        • last reset time
        • fatigue counters
    """

    def __init__(self):
        self.state = {
            "last_anchors": [],
            "last_tone": None,
            "last_hijinx": None,
            "last_reset_ts": 0,
            "fatigue": {
                "chip": 0,
                "reef": 0,
                "lawson": 0,
                "bond": 0,
                "vega": 0,
                "bitsy": 0
            }
        }
        self.load()

    # ------------------------------------------------------
    def load(self):
        if not os.path.exists(STATE_FILE):
            return
        try:
            with open(STATE_FILE, "r") as f:
                self.state = json.load(f)
        except:
            pass

    # ------------------------------------------------------
    def save(self):
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w") as f:
            json.dump(self.state, f, indent=2)
        os.replace(tmp, STATE_FILE)

    # ------------------------------------------------------
    def update_last_anchors(self, anchors):
        self.state["last_anchors"] = anchors
        self.save()

    def update_last_tone(self, tone):
        self.state["last_tone"] = tone
        self.save()

    def update_last_hijinx(self, hijinx):
        self.state["last_hijinx"] = hijinx
        self.save()

    def update_reset(self):
        self.state["last_reset_ts"] = time.time()
        self.save()

    # ------------------------------------------------------
    def get(self, key, default=None):
        return self.state.get(key, default)
