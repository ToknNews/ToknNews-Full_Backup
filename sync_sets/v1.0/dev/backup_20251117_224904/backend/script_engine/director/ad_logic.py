#!/usr/bin/env python3
"""
TOKNNews — Ad Logic (Simple Deterministic)
Module C-7
"""

def should_insert_ad(cycle_index: int) -> bool:
    # Every 5 segments is safe default
    return cycle_index > 0 and cycle_index % 5 == 0
