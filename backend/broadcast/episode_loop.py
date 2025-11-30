#!/usr/bin/env python3
"""
episode_loop.py
TOKEN NEWS — 20-Minute Autonomous Broadcast Loop

Responsibilities:
 - Trigger a full episode generation every cycle_interval seconds
 - Use episode_runner.run_episode() to build scenes + audio
 - Log cleanly
 - Survive exceptions without terminating (PM2-friendly)
 - Prevent overlapping runs
"""

import time
import traceback
import os
from script_engine.episode_runner import run_episode

CYCLE_INTERVAL_SEC = 20 * 60   # 20 minutes
LOCK_FILE = "/opt/toknnews/.episode_loop_lock"


def safe_log(message: str):
    """Prints with timestamp for PM2 logs."""
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    print(f"[EpisodeLoop] [{ts}] {message}")


def loop_already_running() -> bool:
    """Prevent two episode loops from running simultaneously."""
    if os.path.exists(LOCK_FILE):
        return True
    return False


def acquire_lock():
    with open(LOCK_FILE, "w") as f:
        f.write(str(time.time()))


def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)


def run_cycle_once():
    """Run a full episode and handle all exceptions."""
    safe_log("Starting 20-minute broadcast cycle...")

    try:
        block_paths = run_episode()

        if block_paths:
            safe_log(f"Episode generated successfully with {len(block_paths)} blocks.")
        else:
            safe_log("Episode generation produced no blocks.")

    except Exception as e:
        safe_log(f"ERROR during episode generation: {e}")
        traceback.print_exc()

    safe_log("Cycle complete.")


def main():
    safe_log("Episode loop started (20-minute cycles).")

    while True:

        # Ensure only one loop ever runs
        if loop_already_running():
            safe_log("WARNING: Loop already running. Skipping cycle.")
        else:
            acquire_lock()
            try:
                run_cycle_once()
            finally:
                release_lock()

        safe_log(f"Sleeping for {CYCLE_INTERVAL_SEC} seconds...")
        time.sleep(CYCLE_INTERVAL_SEC)


if __name__ == "__main__":
    main()
