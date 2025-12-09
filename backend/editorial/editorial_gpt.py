#!/usr/bin/env python3
"""
editorial_gpt.py — Editorial Engine v4

Central GPT summarization module for ToknNews.

Responsibilities:
  - Convert a raw normalized + fused-signal story into a
    high-quality editorial summary suitable for anchors.
  - Enforce style constraints (ToknNews tone system)
  - Respect LateNight / Chaos modes
  - Zero hallucinations: Only transform provided information.

This module DOES NOT search the internet.
"""

from openai import OpenAI
import os

# Load API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


# =====================================================================
# TOKNNEWS STYLISTIC RULESET
# =====================================================================

BASE_STYLE = """
Write a concise 2–4 sentence editorial summary.
Must follow ToknNews style:
- No cringe hype.
- No predictions.
- No hallucinated facts.
- Use calm, analytical broadcaster voice.
- Reference ONLY the details provided.
"""

LATENIGHT_STYLE = """
Add subtle LateNight energy:
- Slightly sharper voice.
- Dry meta humor is allowed.
- Keep professionalism intact.
"""


# =====================================================================
# SUMMARY ENGINE
# =====================================================================

def summarize_story(
    headline: str,
    body: str = "",
    domain: str = "",
    signals: dict = None,
    latenight: bool = False
) -> str:
    """
    GPT-based editorial summarizer.

    Inputs:
      headline (str): Required
      body (str): Optional raw text
      domain (str): markets/defi/ai/etc
      signals (dict): fused quant signals
      latenight (bool): True = LateNight tone overlay

    Returns:
      summary (str)
    """

    if not client:
        print("[GPT] ERROR: No OpenAI API key available.")
        return headline  # fallback

    # Safety: Build signal notes
    signal_lines = []
    if signals:
        for k, v in signals.items():
            if isinstance(v, dict):
                continue
            signal_lines.append(f"- {k}: {v}")

    signal_blob = "\n".join(signal_lines)

    style_block = BASE_STYLE
    if latenight:
        style_block += LATENIGHT_STYLE

    prompt = f"""
{style_block}

Headline:
{headline}

Context:
{body}

Signals:
{signal_blob}

Domain: {domain}

Write a clean editorial summary that:
- Helps anchors explain the situation.
- Includes the most important implications.
- Does NOT repeat the headline verbatim.
    """

    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.25,
            max_tokens=160
        )

        out = rsp.choices[0].message.content.strip()
        return out

    except Exception as e:
        print("[GPT] Summary failed:", e)
        return headline  # safe fallback


# =====================================================================
# DEMO
# =====================================================================
if __name__ == "__main__":
    test = summarize_story(
        headline="Bitcoin dips 4% as traders rotate into Solana after major whale migration.",
        body="Whales moved 20,000 SOL in a set of rapid transactions.",
        domain="markets",
        signals={
            "price_trend": "down",
            "volume_spike": True,
            "whale_activity": True,
            "gas_pressure": False,
            "liquidity_pressure": True,
            "composite_heat": 8,
        },
        latenight=True
    )
    print("\n=== SUMMARY DEMO ===")
    print(test)
