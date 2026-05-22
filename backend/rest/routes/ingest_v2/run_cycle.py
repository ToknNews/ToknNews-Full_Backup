#!/usr/bin/env python3
"""
run_cycle.py
ToknNews — Canonical Ingestion Orchestrator

Responsibilities:
- Provide a single, authoritative entrypoint for ingestion
- Wrap run_ingestion() with consistent logging and exit codes
- Avoid any dependency on story payloads or counts

Contract:
- run_ingestion() returns True on success, False on failure
"""

import sys
import traceback

from backend.rest.routes.ingest_v2.ingest_controller import run_ingestion


def main():
    print("\n===============================")
    print("[RUN_CYCLE] ToknNews Ingestion Start")
    print("===============================\n")

    try:
        success = run_ingestion()
    except Exception:
        print("[RUN_CYCLE] FATAL ERROR:")
        traceback.print_exc()
        sys.exit(1)

    if not success:
        print("[RUN_CYCLE] WARNING: Ingestion reported failure.")
        sys.exit(2)

    print("[RUN_CYCLE] Ingestion completed successfully.")
    print("[RUN_CYCLE] Done.\n")
    return 0


# --------------------------------------------------
# Backward compatibility for PM2 / legacy callers
# --------------------------------------------------
def run_cycle():
    return main()


if __name__ == "__main__":
    sys.exit(main())
