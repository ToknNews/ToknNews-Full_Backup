#!/usr/bin/env python3
"""
api_rate_limiter.py
TOKEN NEWS — Centralized API throttle manager

Features:
 - Per-source request interval limits
 - Domain-level cooldown
 - Exponential backoff (for 429)
 - Auto-disable after repeated failures
"""

import time


# ============================================================
# RATE LIMIT CONFIG
# ============================================================

SOURCE_LIMITS = {
    "marketaux":  120,     # 1 request / 2 minutes
    "newsdata":   180,     # 1 request / 3 minutes
    "cryptopanic": 90,     # 1 request / 1.5 minutes
    "moralis":    60,      # 1 request / minute
    "rss":        30,      # 1 request / 30s (RSS is cheap)
}

# Domain-level moderation
DOMAIN_LIMITS = {
    "markets":   180,
    "macro":     120,
    "defi":      120,
    "ai":        120,
    "regulation": 300,
    "culture":   300
}

# Backoff
BACKOFF_MULTIPLIER = 2
MAX_BACKOFF = 600  # max 10 minutes


# Internal state
_last_source_call = {}
_last_domain_call = {}
_source_backoff = {}


# ============================================================
# RATE LIMIT CHECKER
# ============================================================

def can_call(source_name: str) -> bool:
    """Returns whether we are allowed to call this API source."""
    now = time.time()

    # Check exponential backoff
    if source_name in _source_backoff:
        wait_until = _source_backoff[source_name]
        if now < wait_until:
            return False

    # Check normal rate limit
    last = _last_source_call.get(source_name, 0)
    limit = SOURCE_LIMITS.get(source_name, 60)

    if now - last < limit:
        return False

    return True


def register_call(source_name: str):
    """Record successful API call."""
    _last_source_call[source_name] = time.time()


def register_failure(source_name: str):
    """Implement exponential backoff on repeated failure."""
    now = time.time()
    prev_backoff = _source_backoff.get(source_name, now)
    next_backoff = min((prev_backoff - now) * BACKOFF_MULTIPLIER + now, now + MAX_BACKOFF)
    _source_backoff[source_name] = next_backoff


# ============================================================
# DOMAIN RATE LIMITER
# ============================================================

def can_use_domain(domain: str) -> bool:
    now = time.time()
    last = _last_domain_call.get(domain, 0)
    limit = DOMAIN_LIMITS.get(domain, 60)

    if now - last < limit:
        return False

    return True


def register_domain(domain: str):
    _last_domain_call[domain] = time.time()
