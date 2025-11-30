#!/usr/bin/env python3
"""
utils/__init__.py — shared helpers (log, etc.)
"""

import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S"
)

def log(message: str):
    """Simple timestamped log used everywhere"""
    print(f"{datetime.now().strftime('%H:%M:%S')} | {message}")
