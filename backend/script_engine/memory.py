#!/usr/bin/env python3
"""
memory.py — Rolling, Intermediate, Long-Term Memory for Token News Anchors
- Rolling: Last 5 lines for immediate chat
- Intermediate: Episode arcs (e.g., "second regulation story")
- Long-Term: Multi-episode narratives (e.g., "Ronin hack pattern")
"""

import json
from pathlib import Path
from datetime import datetime
from collections import deque

MEMORY_DIR = Path("/opt/toknnews/data/memory")
MEMORY_DIR.mkdir(exist_ok=True)

class TokenNewsMemory:
    def __init__(self):
        self.rolling = deque(maxlen=5)  # Last 5 lines
        self.episode_arcs = {}  # e.g., {'regulation': 2, 'defi': 1}
        self.long_term = self._load_long_term()  # Multi-episode facts

    def _load_long_term(self):
        long_term_file = MEMORY_DIR / "long_term.json"
        if long_term_file.exists():
            with open(long_term_file) as f:
                return json.load(f)
        return {"narratives": {}, "facts": {}, "episode_count": 0}

    def _save_long_term(self):
        long_term_file = MEMORY_DIR / "long_term.json"
        with open(long_term_file, "w") as f:
            json.dump(self.long_term, f, indent=2)

    def add_line(self, speaker, text, domain):
        self.rolling.append({"speaker": speaker, "text": text, "domain": domain})
        self.episode_arcs[domain] = self.episode_arcs.get(domain, 0) + 1

    def get_context_for_task(self, task_type, persona, headline, domain):
        context = {
            "rolling_memory": list(self.rolling),
            "arc_count": self.episode_arcs.get(domain, 0),
            "long_term_narratives": self.long_term.get("narratives", {}),
            "episode_count": self.long_term.get("episode_count", 0)
        }

        if task_type in ["pushback", "comeback"]:
            if self.rolling:
                context["previous_take"] = self.rolling[-1]["text"][:100]
                context["previous_speaker"] = self.rolling[-1]["speaker"]

        if "regulation" in domain and self.episode_arcs.get("regulation", 0) > 1:
            context["arc_note"] = f"This is the {self.episode_arcs['regulation']}th regulation story this episode — tie to the pattern."

        if self.long_term.get("narratives", {}).get(domain, []):
            context["long_term"] = self.long_term["narratives"][domain][-1][:150]

        return context

    def save_episode(self, episode_id, domains_used):
        self.long_term["episode_count"] += 1
        self.long_term["narratives"] = {d: self.long_term["narratives"].get(d, []) + [f"Episode {self.long_term['episode_count']}: {domains_used}"] for d in domains_used}
        self._save_long_term()
