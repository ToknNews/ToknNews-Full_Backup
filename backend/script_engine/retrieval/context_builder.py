#!/usr/bin/env python3
"""
retrieval/context_builder.py
Single place where ALL external context gets merged.
Future-proof: add Moralis, Nansen, Dune, 𝕏, memory — just drop in a function.
"""

def build_retrieval_context(story, episode_memory=""):
    parts = []
    
    # 1. Full article
    if story.get("full_text"):
        parts.append(f"FULL ARTICLE:\n{story['full_text'][:7000]}")
    
    # 2. On-chain data (Moralis/Nansen/Dune will go here later)
    if story.get("onchain_context"):
        parts.append(f"ON-CHAIN RIGHT NOW:\n{story['onchain_context']}")
    
    # 3. 𝕏 threads (coming in Step 4)
    if story.get("x_threads"):
        parts.append(f"HOTTEST TAKES ON X:\n{story['x_threads']}")
    
    # 4. Episode memory (coming in Step 5)
    if episode_memory:
        parts.append(f"WE ALREADY SAID TONIGHT:\n{episode_memory}")
    
    # Final merged context — fed directly to Grok
    return "\n\n".join(parts) if parts else "No external context available."
