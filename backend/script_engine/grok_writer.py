#!/usr/bin/env python3
import random
from script_engine.grok_client import grok_complete

def write_line_safe(task_type, persona, headline, synthesis="", scene_state=None, block_index=0, episode_id="unknown", max_words=None):
    scene_state = scene_state or {}
    prev = scene_state.get("previous_line", {}).get("text", "")[-100:] if scene_state else ""

    # STAGE 3 LIVE DATA
    stage3 = scene_state.get("story", {}).get("stage3_context", {})
    context_lines = []

    if stage3.get("dexscreener"):
        top = stage3["dexscreener"][0]
        context_lines.append(f"DEXSCREENER #1: {top['pair']['baseToken']['symbol']} ${top.get('priceUsd', '?')} ({top['priceChange']['h24']}%)")

    if stage3.get("coingecko_trending"):
        top = stage3["coingecko_trending"][0]["item"]
        context_lines.append(f"COINGECKO TRENDING: {top['name']} #{top.get('market_cap_rank', '?')}")

    if stage3.get("birdeye_solana"):
        top = stage3["birdeye_solana"][0]
        context_lines.append(f"SOLANA VOLUME: {top['symbol']} ${top.get('v24hUSD', 0):,.0f}")

    if stage3.get("pumpfun_launches"):
        top = stage3["pumpfun_launches"][0]
        context_lines.append(f"PUMP.FUN NEW: {top['symbol']} launched {int(time.time()-top['created_timestamp'])}s ago")

    if stage3.get("defillama_tvl"):
        top = stage3["defillama_tvl"][0]
        context_lines.append(f"TVL LEADER: {top['name']} ${top.get('tvl', 0):,.0f}")

    live_context = "\n".join(context_lines[:4]) if context_lines else "No live data."

    prompt = f"""You are {persona} on Token News — live desk.
Task: {task_type.replace('_', ' ')}
Headline: {headline}
Previous line: "{prev}"

LIVE ALPHA RIGHT NOW:
{live_context}

Rules:
- NEVER use: hey everyone, let's dive in, frankly, to be honest
- Max {max_words or 28} words
- Reference live data when relevant
- Sound 100% human
- ONLY the spoken line

Write:"""

    try:
        response = grok_complete([{"role": "user", "content": prompt}], temperature=0.88)
        line = response.split("\n")[0].strip(' "\'')
        if max_words:
            line = " ".join(line.split()[:max_words])
        return line
    except Exception as e:
        return f"[{persona}: signal lost]"
