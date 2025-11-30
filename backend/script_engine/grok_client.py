import os
import os
from pathlib import Path
env_path = Path("/opt/toknnews/.env")
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if "=" in line and not line.startswith("#") :
            key, val = line.strip().split("=", 1)
            os.environ[key] = val

import httpx
from loguru import logger

XAI_API_KEY = os.getenv("XAI_API_KEY")
if not XAI_API_KEY:
    raise ValueError("XAI_API_KEY not set")

client = httpx.Client(
    base_url="https://api.x.ai/v1",
    headers={"Authorization": f"Bearer {XAI_API_KEY}"},
    timeout=90.0,
    verify=False  # bypass SSL for now — safe for this endpoint
)

def grok_complete(messages, temperature=0.7, max_tokens=512):
    payload = {
        "model": "grok-3",
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False
    }
    logger.info(f"Grok ← {messages[-1]['content'][:80]}...")
    resp = client.post("/chat/completions", json=payload)
    if resp.status_code != 200:
        logger.error(f"Grok API error {resp.status_code}: {resp.text}")
        resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]
