#!/usr/bin/env python3
"""
ToknNews Automated Cycle — LIVE EDITION
Runs repeatedly under PM2.
Handles:
 - Unified ingestion (RSS + Reddit + APIs)
 - Scene compiler
 - Heartbeat update
"""

import os, json, time, subprocess, datetime

ROOT = "/var/www/toknnews-live/backend/live"
DATA = "/var/www/toknnews-live/data"
LOG  = f"{DATA}/logs/cycle.log"

os.makedirs(os.path.dirname(LOG), exist_ok=True)

def log(msg):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] {msg}\n"
    print(line, end="")
    with open(LOG, "a") as f:
        f.write(line)

def run_cmd(cmd):
    log(f"→ {cmd}")
    subprocess.run(cmd, shell=True)

def update_heartbeat(status="success", error=None):
    hb_path = f"{DATA}/heartbeat.json"
    os.makedirs(DATA, exist_ok=True)

    heartbeat = {
        "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
        "status": status,
        "last_error": error or "",
        "system_uptime": os.popen("uptime -p").read().strip()
    }

    with open(hb_path, "w") as f:
        json.dump(heartbeat, f, indent=2)

    log(f"🩺 Heartbeat updated ({status})")

# ————————————————————————————————————————
# MAIN CYCLE LOOP
# ————————————————————————————————————————

while True:
    try:
        # 1. INGESTION
        run_cmd(f"python3 {ROOT}/hybrid_ingestor.py")

        # 2. COMPILER
        run_cmd(f"python3 {ROOT}/scene_compiler_live.py")

        # 3. HEARTBEAT UPDATE
        update_heartbeat("success")

    except Exception as e:
        log(f"❌ Error during cycle: {e}")
        update_heartbeat("error", error=str(e))

    # Sleep between cycles (customize as needed)
    time.sleep(60)
