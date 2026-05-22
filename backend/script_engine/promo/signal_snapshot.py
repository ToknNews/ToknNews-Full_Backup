#!/usr/bin/env python3
"""
# ============================================================
# 🧩 TOKNNEWS — PROMO FACT SNAPSHOT ENGINE
# ============================================================
#
# ████████╗ ██████╗ ██╗  ██╗███╗   ██╗███╗   ██╗███████╗██╗    ██╗███████╗
# ╚══██╔══╝██╔═══██╗██║ ██╔╝████╗  ██║████╗  ██║██╔════╝██║    ██║██╔════╝
#    ██║   ██║   ██║█████╔╝ ██╔██╗ ██║██╔██╗ ██║█████╗  ██║ █╗ ██║███████╗
#    ██║   ██║   ██║██╔═██╗ ██║╚██╗██║██║╚██╗██║██╔══╝  ██║███╗██║╚════██║
#    ██║   ╚██████╔╝██║  ██╗██║ ╚████║██║ ╚████║███████╗╚███╔███╔╝███████║
#    ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═══╝╚══════╝ ╚══╝╚══╝ ╚══════╝
#
# File: signal_snapshot.py
#
# Purpose:
# - Provide deterministic, real-time promo facts
# - Integrate ToknClaw active narrative clusters
# - Serve as the truth layer for promo generation
#
# ============================================================
"""



import os
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import requests

from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path("/opt/toknnews/.env"))

COINGECKO_URL = "https://api.coingecko.com/api/v3/coins/markets"

CLUSTER_API_URL = os.getenv("TOKNCLAW_CLUSTER_ACTIVE_URL", "")
CLUSTER_PATH = os.getenv(
    "TOKNCLAW_CLUSTER_ACTIVE_PATH",
    "/opt/toknnews/data/ingestion/cluster_active.json",
)

def fetch_top_movers(limit: int = 3) -> List[Dict[str, Any]]:
    try:
        r = requests.get(
            COINGECKO_URL,
            params={
                "vs_currency": "usd",
                "order": "price_change_percentage_24h_desc",
                "per_page": limit,
                "page": 1,
            },
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()

        movers: List[Dict[str, Any]] = []
        for coin in data[:limit]:
            movers.append({
                "name": coin.get("name"),
                "symbol": str(coin.get("symbol", "")).upper(),
                "change_24h": round(float(coin.get("price_change_percentage_24h") or 0), 2),
            })
        return movers
    except Exception:
        return []

def fetch_headline() -> str | None:
    key = os.getenv("MARKETAUX_API_KEY")
    if not key:
        return None

    try:
        r = requests.get(
            "https://api.marketaux.com/v1/news/all",
            params={
                "filter_entities": "BTC,ETH,crypto,blockchain",
                "language": "en",
                "api_token": key,
                "limit": 5,  # 🔴 get a few to filter properly
            },
            timeout=10,
        )

        if r.status_code != 200:
            return None

        data = r.json()
        items = data.get("data") or []

        if not items:
            return None

        # 🔴 keyword filter (strict enough, not overkill)
        keywords = ("bitcoin", "btc", "ethereum", "eth", "crypto", "blockchain")

        for item in items:
            title = (item.get("title") or "").strip()
            if not title:
                continue

            t = title.lower()

            # 🔴 ensure relevance
            if any(k in t for k in keywords):
                return title

        # 🔴 fallback: nothing relevant found
        return None

    except Exception:
        return None

def load_cluster_snapshot():
    # 🔴 API FIRST
    if CLUSTER_API_URL:
        try:
            r = requests.get(CLUSTER_API_URL, timeout=10)

            if r.status_code == 200:
                data = r.json()

                if not isinstance(data, dict):
                    return {}

                # ToknClaw full_state shape:
                # {
                #   "clusters": { "crypto": [...], "macro": [...], ... }
                # }
                clusters = data.get("clusters")

                if isinstance(clusters, dict):
                    return {"clusters": clusters}

                return {}

        except Exception:
            pass

    # 🔴 FALLBACK TO LOCAL FILE
    path = Path(CLUSTER_PATH)

    if not path.exists():
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data if isinstance(data, dict) else {}

    except Exception:
        return {}

def _get_grouped_clusters(cluster_data: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Expected active file shape:
    {
        "generated_at": "...",
        "cluster_count": 4,
        "clusters": {
            "crypto": [...],
            "macro": [...],
            "regulation": [...],
            "markets": [...]
        }
    }
    """
    grouped = cluster_data.get("clusters")

    if isinstance(grouped, dict):
        return grouped

    # Fallback for older root-grouped shape
    if all(isinstance(cluster_data.get(k), list) for k in ("crypto", "macro", "regulation", "markets")):
        return {
            "crypto": cluster_data.get("crypto", []),
            "macro": cluster_data.get("macro", []),
            "regulation": cluster_data.get("regulation", []),
            "markets": cluster_data.get("markets", []),
        }

    return {}

def clean_cluster_title(title: str, headlines: list[str]) -> str:
    """
    Convert raw cluster titles into broadcast-quality narrative titles.
    """
    if not title and headlines:
        return headlines[0]

    if not title:
        return "Market Development"

    t = title.lower()

    # 🔴 Pattern-based normalization
    if "kraken" in t and "extort" in t:
        return "Kraken Faces Active Extortion Threat"

    if "tether" in t and "wallet" in t:
        return "Tether Launches Self-Custody Wallet"

    if "bitcoin" in t and "price" in t:
        return "Bitcoin Surges on Short Liquidations"

    if "deutsche" in t and "kraken" in t:
        return "Deutsche Börse Invests in Kraken"

    # 🔴 fallback → use first strong headline
    if headlines:
        return headlines[0]

    # 🔴 last fallback → clean title casing
    return title.strip().title()

def clean_summary(text: str | None) -> str | None:
    if not text:
        return None

    t = text.strip()

    # 🔴 remove boilerplate
    if "The post" in t:
        t = t.split("The post")[0].strip()

    # 🔴 remove trailing fragments
    if t.endswith("..."):
        t = t[:-3]

    # 🔴 cap length
    if len(t) > 240:
        t = t[:240].rsplit(" ", 1)[0]

    return t

def extract_top_narratives(cluster_data, limit=5, offset=0):
    grouped = cluster_data.get("clusters", {})

    if not isinstance(grouped, dict):
        return []

    all_clusters = []

    for domain in ["crypto", "macro", "regulation", "markets"]:
        clusters = grouped.get(domain, [])
        if isinstance(clusters, list):
            all_clusters.extend(clusters)

    if not all_clusters:
        return []

    # sort by score (importance)
    all_clusters.sort(key=lambda x: float(x.get("score") or 0), reverse=True)

    # 🔴 ROTATION LOGIC
    rotated = all_clusters[offset:] + all_clusters[:offset]

    result = []

    for c in rotated:

        items = c.get("items") or []

        news_items = [
            i for i in items
            if isinstance(i, dict)
            and i.get("layer") == "news"
        ]

        if not news_items:
            continue

        headlines = [
            i.get("title")
            for i in news_items[:3]
            if i.get("title")
        ]

        if not headlines:
            continue

        result.append({
            "title": c.get("title"),
            "domain": c.get("domain"),
            "headlines": headlines,
            "summary": news_items[0].get("summary"),
            "score": c.get("score"),
            "source_count": c.get("source_count"),
            "item_count": len(news_items),
            "narrative_line": headlines[0]
        })

        if len(result) >= limit:
            break

    return result

def build_snapshot() -> Dict[str, Any]:
    snapshot: Dict[str, Any] = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "top_movers": [],
        "headline": None,
        "narratives": [],
    }

    snapshot["top_movers"] = fetch_top_movers()
    snapshot["headline"] = fetch_headline()

    cluster_data = load_cluster_snapshot()
    snapshot["narratives"] = extract_top_narratives(
        cluster_data,
        limit=5,
    )

    return snapshot
