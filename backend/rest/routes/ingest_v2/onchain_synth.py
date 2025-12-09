#!/usr/bin/env python3
"""
onchain_synth.py
ToknNews — On-Chain Movement Synthesizer v1

Goal:
- Take a batch of enriched stories
- Identify on-chain related items
- Synthesize them into ONE cohesive "on-chain movement" story
- Avoid rapid-fire, repetitive micro-headlines
"""

from collections import Counter

# Sources / domains that we treat as on-chain-ish
ONCHAIN_SOURCES = {
    "onchain", "moralis", "etherscan", "solscan",
    "dexscreener", "birdeye", "rpc", "onchain_api"
}

def _is_onchain_story(story: dict) -> bool:
    if not isinstance(story, dict):
        return False
    src = (story.get("source") or "").lower()
    dom = (story.get("domain") or "").lower()
    # crude but safe classification
    if dom == "onchain":
        return True
    if src in ONCHAIN_SOURCES:
        return True
    # fallback: simple keyword scan
    h = (story.get("headline") or "").lower()
    if any(k in h for k in ["on-chain", "onchain", "gas fee", "dex volume", "whale", "wallet", "liquidation"]):
        return True
    return False


def synthesize_onchain_segment(stories: list, show_mode: str = "NEWS") -> dict | None:
    """
    Given a list of enriched stories, return ONE synthesized on-chain movement story
    or None if there is not enough signal.

    We keep this GPT-free for now: pure heuristic summarization.
    """

    onchain_stories = [s for s in stories if _is_onchain_story(s)]
    if len(onchain_stories) < 3:
        # not enough signal to warrant a dedicated segment
        return None

    # Count domains / sources / assets to build a trader-desk style summary
    domains = Counter((s.get("domain") or "onchain").lower() for s in onchain_stories)
    sources = Counter((s.get("source") or "api").lower() for s in onchain_stories)

    # Try to extract token symbols from headlines (very simple heuristic)
    tokens = []
    for s in onchain_stories:
        h = (s.get("headline") or "")
        # crude token extraction: uppercase words of length 2-6
        for w in h.split():
            w_clean = w.strip().strip(",.!?;:()[]")
            if len(w_clean) <= 6 and w_clean.isupper() and w_clean.isalpha():
                tokens.append(w_clean)
    token_counts = Counter(tokens)

    # Build a trader-desk framing
    total = len(onchain_stories)
    top_domains = ", ".join(d for d, _ in domains.most_common(2)) or "onchain"
    top_tokens = ", ".join(t for t, _ in token_counts.most_common(4)) or "key assets"

    # === HEADLINE ===
    if show_mode.upper() == "LATENIGHT":
        headline = "LateNight On-Chain: Flows, Whales, and Weirdness"
    else:
        headline = "On-Chain Trader Desk Update"

    # === SUMMARY ===
    parts = []

    parts.append(
        f"We're tracking {total} on-chain signals across {top_domains} right now."
    )

    if token_counts:
        parts.append(
            f"Standout activity includes {top_tokens}, with unusual flows and positioning."
        )

    if "moralis" in sources:
        parts.append("Moralis data shows shifting wallet behavior and liquidity pockets moving.")
    if "etherscan" in sources:
        parts.append("Etherscan traces highlight large transfers and gas pressure on Ethereum.")
    if "birdeye" in sources or "dexscreener" in sources:
        parts.append("DEX views flag rising volume and rotation between majors and midcaps.")
    if "solscan" in sources:
        parts.append("Solana trackers hint at active traders rotating through higher beta names.")

    # collapse into one paragraph
    summary = " ".join(parts)

    # anchors: Ledger primary, Reef secondary, Cash tertiary for trader psychology
    anchors = ["ledger", "reef", "cash"]

    # importance: scale with total count
    importance = min(10.0, 6.5 + total * 0.1)

    synthesized_story = {
        "headline": headline,
        "summary": summary,
        "domain": "onchain",
        "sentiment": "Neutral",
        "importance": round(importance, 1),
        "anchors": anchors,
        "source": "onchain_synth_v1",
        "timestamp": onchain_stories[-1].get("timestamp"),
        "breaking": False,
        "raw_onchain_count": total
    }

    return synthesized_story


if __name__ == "__main__":
    print("onchain_synth_v1 loaded.")
