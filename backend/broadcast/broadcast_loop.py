#!/usr/bin/env python3
"""
ToknNews Broadcast Loop (v1)

This is the unified orchestrator:
- Runs ingestion + compiler
- Hands results to ProgrammingDirector
- Dispatches segments to Script Engine v3
- Emits completed broadcast blocks to /data/broadcast/
"""
import sys, os

# Correct module base path
BACKEND_DIR = "/var/www/toknnews-repo/backend"
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import os
import json
import time
from datetime import datetime

from script_engine.script_engine_v3 import generate_script
from script_engine.director.director_brain import ProgrammingDirector
from script_engine.audio.audio_block_renderer import render_script_sequence
from script_engine.audio.processor.mixer import mix_audio_blocks

CURRENT_EPISODE_BLOCKS = []

# Paths
BASE = "/var/www/toknnews-live"
DATA = f"{BASE}/data"
LIVE_BACKEND = f"{BASE}/backend/live"

os.makedirs(f"{DATA}/broadcast", exist_ok=True)

# Instantiate Programming Director
PD = ProgrammingDirector()
# Patch: initialize PD timing so resets and segments behave naturally
from datetime import datetime, timedelta

now = datetime.utcnow()
PD.state.last_intro_time = now - timedelta(minutes=20)
PD.state.last_reset_time = now - timedelta(minutes=20)
PD.state.last_banter_time = now - timedelta(minutes=10)
PD.state.last_ad_time = now - timedelta(minutes=10)
PD.state.last_promo_time = now - timedelta(minutes=10)

# Give PD some segment history so it doesn't think show just started
PD.state.segment_history = ["news", "news", "panel"]

# Escalation baseline for testing
PD.state.escalation_level = 3

def write_broadcast_block(block):
    """
    Saves each generated broadcast block as an atomic JSON file.
    """
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    out_path = f"{DATA}/broadcast/block_{ts}.json"

    with open(out_path, "w") as f:
        json.dump(block, f, indent=2)

    print(f"[Broadcast] ✔ Wrote block → {out_path}")
    return out_path

def cycle_once():
    """
    Runs a full ingest → compile → PD segment → script engine cycle.
    """

    print("\n===== NEW BROADCAST CYCLE =====")

    # 1. INGESTION
    #os.system(f"python3 {LIVE_BACKEND}/hybrid_ingestor.py")

    # 2. COMPILE SCENES
    #os.system(f"python3 {LIVE_BACKEND}/scene_compiler_live.py")

    # 3. LOAD latest scene
    latest_path = f"{DATA}/latest_scene.json"
    if not os.path.exists(latest_path):
        print("[Broadcast] ⚠ No latest_scene.json found.")
        return

    with open(latest_path, "r") as f:
        latest = json.load(f)

    # --- Apply reset suppression before evaluating ---
    if getattr(PD.state, "reset_suppression_cycles", 0) > 0:
        print(f"[PD] 🔇 Reset suppression active ({PD.state.reset_suppression_cycles} cycles left)")

    # 4. PD DECIDES WHAT SEGMENT TO RUN
    seg = PD.evaluate(
        story_queue=[latest],
        last_segment_result=PD.state.last_segment
    )

    print(f"[Director] → Selected segment: {seg}")

    # --- Decrement reset suppression cycles after each evaluation ---
    if PD.state.reset_suppression_cycles > 0:
        PD.state.reset_suppression_cycles -= 1
        print(f"[PD] 🔽 Suppression decremented → {PD.state.reset_suppression_cycles} cycles left")
    else:
        print("[PD] No reset suppression active")

    # --- RESET HANDLER (PD-triggered chip_reset) ---
    if isinstance(seg, dict) and seg.get("type") == "chip_reset":
        print("[Broadcast] → RESET EVENT TRIGGERED — Executing Chip Reset Sequence")

        script = generate_script(seg)   # PD already sent correct payload

        write_broadcast_block(script)
        PD.state.last_segment = "chip_reset"
        return

    # 5. Script Engine block — PD payload normalization

    # NEWS (default path)
    if seg == "news":
        payload = latest

    # HIJINX (vega_pad)
    elif seg == "vega_pad":
        payload = {
            "type": "vega_pad",
            "hijinx_line": PD.state.hijinx_line
        }

    # BITSY META INTERRUPTION
    elif seg == "bitsy_meta":
        payload = {
            "type": "bitsy_meta",
            "line": PD.state.hijinx_line   # PD stores bitsy_line in hijinx handler
        }

    # EXPOSÉ / PANEL / BANTER OR ANY OTHER SEGMENT
    else:
        payload = {
            "type": seg,
            **latest
        }

    # 5B. Generate script for NON-reset segments
    script = generate_script(payload)

    # Normalize_script structure
    block = script if "script_sequence" in script else {"script_sequence": script}

    # === AUDIO RENDERING (D-5-4) ===
    script_seq = block.get("script_sequence", [])
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    audio_batch = render_script_sequence(script_seq, session_tag=ts)

    # === MIX FINAL SEGMENT AUDIO ===
    segment_mix_path = mix_audio_blocks(audio_batch)
    block["segment_mix"] = segment_mix_path

    # Attach audio metadata
    block["audio_files"] = audio_batch

    # 6. Save broadcast block
    out_path = write_broadcast_block(block)
    PD.state.last_segment = seg
    PD.state.segment_history.append(seg)

    # Add this block to current episode buffer
    global CURRENT_EPISODE_BLOCKS
    CURRENT_EPISODE_BLOCKS.append(out_path)

    # End-of-show trigger (for now: every 10 blocks)
    if len(CURRENT_EPISODE_BLOCKS) >= 10:
        from broadcast.show_assembler.assembler import assemble_show
        episode_path = assemble_show(CURRENT_EPISODE_BLOCKS)
        print(f"[Broadcast] 🎬 Episode assembled → {episode_path}")
        CURRENT_EPISODE_BLOCKS = []

def main_loop():
    """
    Infinite broadcast loop.
    Adjust timing as needed.
    """
    while True:
        try:
            cycle_once()
        except Exception as e:
            print(f"[Broadcast] ❌ Error: {e}")
        time.sleep(10)   # adjust run frequency later


if __name__ == "__main__":
    main_loop()
