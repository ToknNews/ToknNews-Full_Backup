#!/usr/bin/env python3
import random

def run_pd(headline="", suggested_anchor=None, story_index=0, total_stories=1):
    # Simple domain detection (you can make this smarter later)
    text = headline.lower()
    if any(x in text for x in ["macro", "fed", "rate", "inflation", "recession", "bond"]):
        domain = "macro"
    elif any(x in text for x in ["regulation", "sec", "tax", "law", "compliance", "delay"]):
        domain = "regulation"
    elif any(x in text for x in ["defi", "dex", "liquidity", "apy", "yield", "lp", "pancakeswap"]):
        domain = "defi"
    elif any(x in text for x in ["onchain", "ledger", "flow", "cohort", "wallet", "cluster"]):
        domain = "onchain"
    elif any(x in text for x in ["retail", "cash", "trader", "sentiment", "fomo", "fud"]):
        domain = "retail"
    elif any(x in text for x in ["hack", "exploit", "recovery", "drain", "security"]):
        domain = "onchain"
    elif any(x in text for x in ["privacy", "houdini", "anonymity", "zero-knowledge"]):
        domain = "privacy"
    else:
        domain = "general"

    # YOUR CANON CAST MAPPING — LOCKED IN
    mapping = {
        "macro":      "BOND",
        "regulation": "BOND",
        "defi":       "REEF",
        "onchain":    "LEDGER",
        "retail":     "CASH",
        "privacy":    "LEDGER",
        "general":    "CHIP"
    }

    primary = mapping.get(domain, "CHIP")
    secondary_options = ["REEF", "BOND", "LEDGER", "CASH", "IVY", "PENNY"]
    secondary = random.choice([s for s in secondary_options if s != primary])

    return {
        "primary_anchor": primary,
        "secondary_anchor": secondary,
        "domain": domain
    }

def get_domain_anchors(domain):
    mapping = {
        "macro": ["BOND", "CHIP"],
        "markets": ["CHIP", "CASH"],
        "regulation": ["BOND", "CHIP"],
        "defi": ["REEF", "LEDGER"],
        "onchain": ["LEDGER", "REEF"],
        "ai": ["BOND", "REEF"],
        "venture": ["REEF", "CASH"],
        "retail": ["CASH", "PENNY"],
        "sentiment": ["IVY", "CASH"],
        "meta": ["BITSY", "REX VOL"],
        "general": ["CHIP", "BOND"]
    }
    return mapping.get(domain, ["CHIP", "BOND"])
