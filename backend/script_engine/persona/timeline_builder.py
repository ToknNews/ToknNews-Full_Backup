#!/usr/bin/env python3
import time
import random
from script_engine.grok_writer import write_line_safe
from script_engine.director.pd_controller import run_pd

def _block(text, speaker, tag):
    return {"speaker": speaker.upper(), "text": text, "tag": tag, "timestamp": time.time()}

def build_timeline(story_clusters: list, daypart: str = "evening", show_mode: str = "NEWS", voice_map: dict = None):
    if voice_map is None:
        from script_engine.persona.voice_map import VOICE_MAP
        voice_map = VOICE_MAP

    timeline = []

    # INTRO
    timeline.append(_block("You're watching Token News.", "vega", "vega_intro"))
    timeline.append(_block(f"Good {daypart}, welcome to Token News.", "chip", "chip_intro"))

    # RUNDOWN
    headlines = [s["headline"].split(":")[0].strip() for s in story_clusters[:8]]
    timeline.append(_block("Here’s what’s ahead:\n" + "\n".join(f"• {h}" for h in headlines), "chip", "chip_rundown"))

    # MAIN LOOP — story object passed to EVERY line
    for idx, story in enumerate(story_clusters):
        pd_cfg = run_pd(headline=story["headline"], story_index=idx, total_stories=len(story_clusters))
        primary = pd_cfg["primary_anchor"]
        if primary == "CHIP":
            primary = random.choice(["REEF", "BOND", "LEDGER", "CASH", "IVY", "PENNY"])
        secondary = pd_cfg["secondary_anchor"]
        if secondary in [primary, "CHIP"]:
            options = ["REEF", "BOND", "LEDGER", "CASH", "IVY", "PENNY"]
            secondary = random.choice([o for o in options if o != primary])

        # THIS IS THE KEY LINE — every Grok call now sees the full story + Stage 3 data
        scene_state = {"story": story}

        # Toss
        timeline.append(_block(f"{primary}, {story['headline'].split(':')[0]} — your read?", "chip", "toss"))

        # Open
        open_line = write_line_safe("open", primary, story["headline"], story.get("summary", ""), scene_state, max_words=32)
        timeline.append(_block(open_line, primary, "open"))

        # Challenge
        challenge_line = write_line_safe("challenge", secondary, story["headline"], f"Counter to: {open_line}", scene_state, max_words=28)
        timeline.append(_block(challenge_line, secondary, "challenge"))

        # Defense
        defense_line = write_line_safe("defense", primary, story["headline"], f"Response to: {challenge_line}", scene_state, max_words=28)
        timeline.append(_block(defense_line, primary, "defense"))

        # Chaos
        reactor = random.choice(["BITSY", "REX VOL"])
        chaos_line = write_line_safe("chaos", reactor, story["headline"], "", scene_state, max_words=12)
        timeline.append(_block(chaos_line, reactor, "chaos"))

        # Wrap + next toss
        next_head = story_clusters[idx+1]["headline"].split(':')[0] if idx+1 < len(story_clusters) else "the wrap-up"
        wrap_line = write_line_safe("wrap", "chip", story["headline"], f"Primary: {open_line[:50]}... Secondary: {challenge_line[:50]}...", scene_state, max_words=35)
        wrap_line += f" {next_head}, you're up."
        timeline.append(_block(wrap_line, "chip", "wrap"))

    # OUTRO
    timeline.append(_block("Thanks everyone — that’s Token News. We'll see you next cycle.", "chip", "outro"))

    return {"blocks": timeline}
