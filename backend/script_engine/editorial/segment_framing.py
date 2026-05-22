"""
segment_framing.py
ToknNews — Segment Order Engine
"""

def frame_segments(stories):

    segments = {
        "market_open": [],
        "onchain_desk": [],
        "macro": [],
        "regulation": [],
        "tech_ai": [],
        "culture": []
    }

    for s in stories:

        domain = s.get("domain")

        if s.get("source") == "toknclaw":
            segments["onchain_desk"].append(s)

        elif domain == "markets":
            segments["market_open"].append(s)

        elif domain == "macro":
            segments["macro"].append(s)

        elif domain == "legal":
            segments["regulation"].append(s)

        elif domain == "ai":
            segments["tech_ai"].append(s)

        else:
            segments["culture"].append(s)

    ordered = (
        segments["market_open"] +
        segments["onchain_desk"] +
        segments["macro"] +
        segments["regulation"] +
        segments["tech_ai"] +
        segments["culture"]
    )

    return ordered
