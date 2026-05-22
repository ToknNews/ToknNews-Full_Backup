#!/usr/bin/env python3
"""
grok_context_injector.py

PRODUCTION MODULE — NO STUBS

PURPOSE:
- Inject real-time editorial context using xAI Grok
- Refine output with OpenAI GPT-4o / mini
- Bounded, optional, and failure-safe

CONTRACT:
Input:
- clusters: List[Dict]

Output:
- Dict[cluster_id, {
      "context": refined_editorial_context,
      "grok_take": raw_grok_output
  }]
"""

from dotenv import load_dotenv
load_dotenv("/opt/toknnews/.env")

import os
import json
import time
import requests
from typing import List, Dict
import openai

# =====================================================
# CONFIG
# =====================================================

XAI_API_KEY = os.getenv("XAI_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
XAI_MODEL = os.getenv("XAI_GROK_MODEL")  # must be grok-4-1-fast-reasoning

if not XAI_API_KEY:
    raise RuntimeError("Missing XAI_API_KEY in environment")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY in environment")

if not XAI_MODEL:
    raise RuntimeError("XAI_GROK_MODEL not set in environment")

openai.api_key = OPENAI_API_KEY

# xAI Responses API (CORRECT)
XAI_API_URL = "https://api.x.ai/v1/responses"

OPENAI_MODEL = os.getenv("TOKN_CONTEXT_MODEL", "gpt-4o-mini")

MAX_CLUSTERS = 5
MAX_STORIES_PER_CLUSTER = 5
MAX_GROK_TOKENS = 800
MAX_OPENAI_TOKENS = 300

HTTP_TIMEOUT = 20
HTTP_RETRIES = 2

# =====================================================
# GROK CONTEXT FETCH (xAI RESPONSES API)
# =====================================================

def fetch_grok_context(cluster: Dict) -> str:
    """
    Fetch real-time context from Grok using xAI Responses API.
    """

    topic = cluster.get("topic", "crypto markets")

    # Runtime verification
    print(f"[GROK] Using model: {XAI_MODEL}")

    payload = {
        "model": XAI_MODEL,
        "input": [
            {
                "role": "system",
                "content": (
                    "You are a real-time crypto, macro, and regulatory intelligence engine. "
                    "You do not speculate. You report current narratives and sentiment."
                )
            },
            {
                "role": "user",
                "content": (
                    f"Topic: {topic}\n\n"
                    "Return concise bullet points covering:\n"
                    "- Current social sentiment\n"
                    "- Macro or regulatory developments\n"
                    "- Market psychology\n\n"
                    "Avoid hype. Avoid predictions."
                )
            }
        ],
        "temperature": 0.2,
        "max_output_tokens": MAX_GROK_TOKENS,
    }

    headers = {
        "Authorization": f"Bearer {XAI_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(HTTP_RETRIES):
        try:
            response = requests.post(
                XAI_API_URL,
                headers=headers,
                json=payload,
                timeout=HTTP_TIMEOUT,
            )
            response.raise_for_status()

            data = response.json()

            # Extract output_text blocks from xAI Responses API
            texts = []

            for item in data.get("output", []):
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        texts.append(content.get("text", ""))

            if not texts:
                raise RuntimeError("Grok response contained no output_text blocks")

            return "\n".join(texts).strip()

        except Exception as e:
            if attempt == HTTP_RETRIES - 1:
                raise RuntimeError(f"Grok API failed: {e}")
            time.sleep(1)

    return ""

# =====================================================
# OPENAI REFINEMENT (UNCHANGED)
# =====================================================

def refine_with_openai(cluster: Dict, grok_context: str) -> str:
    """
    Refine Grok output into editorial-grade context.
    """

    stories = cluster.get("stories", [])[:MAX_STORIES_PER_CLUSTER]
    story_snippets = "\n".join(
        f"- {s.get('text', '')[:200]}" for s in stories
    )

    prompt = (
        "You are an editorial analyst for ToknNews.\n\n"
        f"Cluster Topic:\n{cluster.get('topic', 'N/A')}\n\n"
        f"Key Stories:\n{story_snippets}\n\n"
        f"Real-Time Context:\n{grok_context}\n\n"
        "Write 1–2 concise paragraphs that:\n"
        "- Explain why this topic matters today\n"
        "- Connect facts with real-time sentiment\n"
        "- Remain neutral and professional\n"
        "- Do NOT invent facts or predictions\n"
    )

    response = openai.ChatCompletion.create(
        model=OPENAI_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4,
        max_tokens=MAX_OPENAI_TOKENS,
    )

    return response.choices[0].message.content.strip()

# =====================================================
# MAIN ORCHESTRATOR
# =====================================================

def generate_context_for_clusters(clusters: List[Dict]) -> Dict[str, Dict[str, str]]:
    """
    Generate editorial context for top clusters.
    """

    context_map: Dict[str, Dict[str, str]] = {}

    if not clusters or not isinstance(clusters, list):
        return context_map

    for cluster in clusters[:MAX_CLUSTERS]:
        cluster_id = cluster.get("cluster_id", "unknown")

        try:
            grok_context = fetch_grok_context(cluster)
            refined_context = refine_with_openai(cluster, grok_context)

            context_map[cluster_id] = {
                "context": refined_context,
                "grok_take": grok_context
            }

        except Exception as e:
            print(f"[GROK][WARN] Context injection failed for {cluster_id}: {e}")
            continue

    return context_map
