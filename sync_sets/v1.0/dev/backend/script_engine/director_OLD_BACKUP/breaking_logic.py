#!/usr/bin/env python3
"""
TOKNNews — Breaking News Logic
Module C-7
"""

def is_breaking(headline: str) -> bool:
    if not headline:
        return False
    h = headline.lower()
    triggers = ["breaking", "urgent", "hack", "exploit", "lawsuit", "sec charges"]
    return any(t in h for t in triggers)
