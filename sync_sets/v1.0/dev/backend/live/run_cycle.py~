#!/usr/bin/env python3
"""
ToknNews Automated Cycle — modern edition
Runs every 20 min under PM2.
"""
import os, subprocess, datetime

ROOT = "/var/www/toknnews/modules"
DATA = "/var/www/toknnews/data"
LOG  = f"{DATA}/logs/auto_cycle.log"

os.makedirs(os.path.dirname(LOG), exist_ok=True)

def run(cmd):
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    line = f"[{ts}] → {cmd}\n"
    print(line, end="")
    with open(LOG, "a") as f:
        f.write(line)
        subprocess.run(cmd, shell=True, stdout=f, stderr=f)

# 1️⃣  Unified ingest (RSS + API + Reddit)
run(f"python3 {ROOT}/hybrid_ingestor.py")

# 2️⃣  Trigger compiler to refresh dashboard snapshot
try:
    print("[System] 🧩 Running scene compiler to update snapshot...")
    subprocess.run(
        ["python3", f"{ROOT}/scene_compiler_live.py"],
        check=True
    )
except Exception as e:
    print(f"[System] ⚠️ Could not run compiler: {e}")

print(f"[{datetime.datetime.now().isoformat(timespec='seconds')}] ✅ ToknNews cycle complete.\n")
