#!/usr/bin/env python3
"""
grok_client.py
ToknNews — Runtime Grok API Client (xAI)

Responsibilities:
- Single abstraction for Grok calls
- Supports Grok tool calling (x_keyword_search, x_semantic_search, browse_page)
- Handles auth, retries, and failures
- Keeps ingestion/enrichment code clean
"""

import os
import time
from xai_sdk import Client
from xai_sdk.chat import system, user

# --------------------------------------------------
# CONFIG
# --------------------------------------------------

XAI_API_KEY = os.getenv("XAI_API_KEY") or os.getenv("GROK_API_KEY")
GROK_MODEL = os.getenv("XAI_GROK_MODEL", "grok-4-1-fast-reasoning")

MAX_RETRIES = 2


class GrokError(Exception):
    pass


# --------------------------------------------------
# CLIENT (SINGLETON)
# --------------------------------------------------

_client = None

def _get_client():
    global _client
    if _client is not None:
        return _client

    if not XAI_API_KEY:
        raise GrokError("XAI_API_KEY not set")

    _client = Client(api_key=XAI_API_KEY)
    return _client


# --------------------------------------------------
# PUBLIC API
# --------------------------------------------------

def call_grok(
    prompt: str = None,
    messages: list = None,
    tools: list = None,
    max_tokens: int = 256,
) -> str:
    """
    Call Grok with optional tool support.

    Args:
        prompt: simple user prompt (string)
        messages: list of xai_sdk.chat message objects (optional)
        tools: list of tool names (e.g. ["x_keyword_search"])
        max_tokens: response token cap
    """

    client = _get_client()
    last_error = None

    for attempt in range(1, MAX_RETRIES + 2):
        try:
            chat = client.chat.create(model=GROK_MODEL)

            # System framing
            chat.append(
                system("You are Grok, providing analysis for ToknNews.")
            )

            if messages:
                for m in messages:
                    chat.append(m)
            elif prompt:
                chat.append(user(prompt))
            else:
                raise GrokError("call_grok requires prompt or messages")

            # 🔑 Tool support
            # 🔑 Tool support
            if tools:
                chat.tools = tools

            # Token control (SDK expects attribute, not argument)
            chat.max_tokens = max_tokens

            response = chat.sample()
            return response.content

        except Exception as e:
            last_error = e
            if attempt <= MAX_RETRIES:
                time.sleep(2 ** attempt)
            else:
                break

    raise GrokError(f"Grok call failed: {last_error}")
