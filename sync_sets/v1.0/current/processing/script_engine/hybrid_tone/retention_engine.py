#!/usr/bin/env python3
"""
TOKNNews — Retention Hook Engine (Strict Deterministic Mode)
Adds light, professional retention hooks without hype.
"""

HOOKS = [
    "More details will matter as this develops.",
    "Worth keeping an eye on as conditions shift.",
    "Several factors may influence this further.",
    "This could evolve depending on liquidity trends."
]

def add_retention_hooks(text: str) -> str:
    """
    Deterministic, non-intrusive hook injection.
    Always appends exactly one hook.
    """

    if not text:
        return text

    # Choose hook based on hash mod to remain deterministic across runs
    index = abs(hash(text)) % len(HOOKS)
    hook = HOOKS[index]

    return f"{text} {hook}"
