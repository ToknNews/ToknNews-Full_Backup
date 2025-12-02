#!/bin/bash
cd /opt/toknnews
source .env
cd /opt/toknnews/backend/live

# Run all source fetchers
python3 toknnews_coindesk_api.py
python3 toknnews_twitter.py
python3 toknnews_market_intel.py

# Merge them
python3 merge_sources.py
