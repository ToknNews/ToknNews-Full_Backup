#!/usr/bin/env python3

import argparse
from backend.script_engine.episode_runner import run_episode

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tokn Episode CLI")
    parser.add_argument("--episode-id", type=str, required=True, help="Episode ID for tracking")
    parser.add_argument("--max-headlines", type=int, default=25, help="Max headlines to ingest")
    parser.add_argument("--skip-ingest", action="store_true", help="Skip news ingest step")
    args = parser.parse_args()

    if not args.skip_ingest:
        from backend.rest.routes.ingest_v2.run_cycle import ingest_news_cycle
        ingest_news_cycle(max_headlines=args.max_headlines)

    run_episode(episode_id=args.episode_id)
