#!/usr/bin/env python3
"""
grok_client.py – Token News → Grok 4 interface
Used by hybrid_line_writer to generate every spoken line
"""

import os
import requests
from script_engine.utils import log

GROK_API_KEY = os.getenv("GROK_API_KEY", "dummy-key-for-dry-run")
GROK_ENDPOINT = "https://api.x.ai/v1/chat/completions"

def query_grok(prompt: str, temperature: float = 0.7, max_tokens: int = 100) -> str:
    """Send prompt to Grok 4 and return response"""
    
    # DRY-RUN MODE — when DISABLE_TTS is on, we fake perfect lines
    if os.getenv("DISABLE_TTS") == "true":
        fake_lines = [
            "Bitcoin just smashed through ninety-three thousand dollars.",
            "This is the fastest bull run we've ever seen.",
            "The ETF money is absolutely nuclear right now.",
            "Someone just bought another billion dollars of Bitcoin.",
            "We're not in Kansas anymore.",
            "Holy liquidity, Batman.",
        ]
        import random
        line = random.choice(fake_lines)
        log(f"[DRY-RUN] Grok would have said: {line}")
        return line

    # Real Grok call (only runs when DISABLE_TTS is off)
    payload = {
        "messages": [{"role": "user", "content": prompt}],
        "model": "grok-4",
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        r = requests.post(GROK_ENDPOINT, json=payload, headers={"Authorization": f"Bearer {GROK_API_KEY}"}, timeout=20)
        r.raise_for_status()
        response = r.json()["choices"][0]["message"]["content"]
        log(f"Grok → {response.strip()}")
        return response.strip()
    except Exception as e:
        log(f"Grok API failed: {e}")
        return "Market conditions are evolving rapidly."

query_grok  # export
