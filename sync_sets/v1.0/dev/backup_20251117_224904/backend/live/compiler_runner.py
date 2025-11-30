#!/usr/bin/env python3
import os, time, subprocess

COMPILE_INTERVAL = 60  # seconds between runs

while True:
    print(f"[Runner] 🕒 Starting compile cycle at {time.strftime('%H:%M:%S')}")
    subprocess.run([
        "python3", "/var/www/toknnews/modules/scene_compiler_live.py",
        "--headline", "Scheduled Live Ingestion"
    ])
    print(f"[Runner] ✅ Compile finished, sleeping {COMPILE_INTERVAL}s...\n")
    time.sleep(COMPILE_INTERVAL)
