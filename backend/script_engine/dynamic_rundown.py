#!/usr/bin/env python3
"""
dynamic_rundown.py
ToknNews — STRICT Thematic Rundown Generator (GPT-4o-mini Compliant)

Forces:
 - 3–5 thematic bullets
 - ZERO headline text
 - ZERO token/project names
 - Natural newsroom phrasing
"""

from openai import OpenAI
from backend.runtime.vault_loader import load_secrets

_secrets = load_secrets()
client = OpenAI(api_key=_secrets.get("openai_api_key","")) if _secrets.get("openai_api_key") else None

PHONETIC_MAP = {
    "BTC": "bee-tee-see",
    "ETH": "ee-th",
    "USDT": "you-ess-dee-tee",
    "USDC": "you-ess-dee-see",
    "ETF": "E-T-F",
    "AI": "A-I",
}

def phonetic(s):
    for k,v in PHONETIC_MAP.items():
        s = s.replace(k, v).replace(k.lower(), v)
    return s


def generate_rundown(story_clusters, pd_context, daypart):

    top = story_clusters[:10]
    headlines = [phonetic(s["headline"]) for s in top]

    if client is None:
        return (
            "Here’s what we’re watching:\n"
            "• Sentiment is shifting across markets.\n"
            "• Traders are reacting to new catalysts.\n"
            "• Liquidity and volatility trends are emerging.\n"
        )

    prompt = f"""
You are writing the on-air rundown for ToknNews.
Chip is speaking.

RAW HEADLINES (DO NOT REPEAT):
{chr(10).join('- ' + h for h in headlines)}

Your strict tasks:

1. DO NOT REPEAT ANY HEADLINE TEXT.
2. DO NOT MENTION ANY TOKEN, PROJECT, COIN, OR ORGANIZATION NAME.
3. DO NOT OUTPUT ANY TICKER SYMBOLS.
4. Transform ALL stories into 3–5 THEMATIC INSIGHTS.
5. ONLY describe market-wide patterns, sentiment shifts, catalysts, or behavioral trends.
6. Bullets must be 1 short sentence each (10–18 words).
7. Output MUST begin with:
   Here’s what we’re watching:
8. Follow with ONLY "•" bullet points.
9. ABSOLUTELY NO direct references to news items.
10. ABSOLUTELY NO proper nouns from crypto.

Examples (GOOD THEMES):
• Market sentiment is shifting as traders rotate into new opportunities.
• Liquidity patterns show cautious optimism despite recent volatility.
• Analysts are watching catalysts that could influence momentum in coming sessions.

Examples (NOT ALLOWED):
• LINK is trending.
• Bitcoin sees a spike.
• Headline #1 says…
• Anything naming tokens, companies, projects, chains, or upgrades.

Now generate exactly the required rundown.
""".strip()

    try:
        rsp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"user","content":prompt}],
            max_tokens=200,
            temperature=0.2,
            timeout=10,
        )
        return rsp.choices[0].message.content.strip()

    except Exception:
        return (
            "Here’s what we’re watching:\n"
            "• Sentiment is shifting across markets.\n"
            "• Traders are reacting to new catalysts.\n"
            "• Liquidity and volatility trends are emerging.\n"
        )


if __name__ == "__main__":
    print("[RUNDOWN] Strict thematic generator loaded.")
