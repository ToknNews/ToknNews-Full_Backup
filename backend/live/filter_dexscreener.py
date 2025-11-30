#!/usr/bin/env python3
"""
ToknNews DexScreener Signal Filter
Keeps only tokens with large moves, volume, or social buzz.
"""

import json, os, time
from datetime import datetime

RAW = "/var/www/toknnews/data/raw/api_latest.json"
OUT = "/var/www/toknnews/data/raw/api_filtered.json"

def filter_signals():
    if not os.path.exists(RAW):
        print("[DexFilter] ⚠️ No raw file found.")
        return

    with open(RAW, "r") as f:
        data = json.load(f)

    filtered = []
    for d in data:
        try:
            # pull basic numeric values
            price = float(d.get("price", 0))
            buys = int(d.get("buys_5m", 0))
            sells = int(d.get("sells_5m", 0))
            score = buys + sells

            # fetch nested info if exists
            pc = d.get("priceChange", {}) if isinstance(d.get("priceChange"), dict) else {}
            h1 = abs(pc.get("h1", 0))
            h24 = abs(pc.get("h24", 0))
            vol = float(d.get("volume", {}).get("h24", 0)) if isinstance(d.get("volume"), dict) else 0

            # compute simple heat score
            signal = min(100, round(
                (h24 * 2) +
                (vol / 1_000_000) +
                (score / 10)
            , 2))
            d["signal_score"] = signal

            if (
                h1 >= 2 or
                h24 >= 5 or
                vol >= 100000 or
                score >= 20
            ):
                filtered.append(d)

        except Exception:
            continue

    # sort by 24h volume desc
    filtered = sorted(filtered, key=lambda x: float(x.get("volume", {}).get("h24", 0)), reverse=True)[:20]

    with open(OUT, "w") as f:
        json.dump(filtered, f, indent=2)

    print(f"[DexFilter] ✅ Wrote {len(filtered)} filtered tokens → {OUT}")

if __name__ == "__main__":
    filter_signals()
