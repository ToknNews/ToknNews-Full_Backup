#!/usr/bin/env python3
"""
run_cycle.py
ToknNews 2025 — Canonical Ingestion Runner (Transfer Brain v1.0)

This is the ONLY ingest runner used by:
 - PM2
 - cron jobs
 - dashboard/manual triggers
 - episode_builder fallback ingestion

All ingestion flows must go through this file to guarantee
synchronous, Transfer-Brain-aligned behavior.

Calls:
    from ingest_controller import run_ingestion
"""

import sys
import traceback

from backend.rest.routes.ingest_v2.ingest_controller import run_ingestion


def main():
    print("\n===============================")
    print("[RUN_CYCLE] ToknNews Ingestion Start")
    print("===============================\n")

    try:
        data = run_ingestion()
    except Exception:
        print("[RUN_CYCLE] FATAL ERROR:")
        traceback.print_exc()
        sys.exit(1)

    if not data:
        print("[RUN_CYCLE] WARNING: Ingestion returned 0 stories.")
        sys.exit(2)

    print(f"[RUN_CYCLE] Ingestion completed successfully → {len(data)} stories")
    print("[RUN_CYCLE] Done.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
