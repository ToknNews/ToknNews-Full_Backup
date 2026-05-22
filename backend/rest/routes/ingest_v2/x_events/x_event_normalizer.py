# x_event_normalizer.py
"""
ToknNews — X Event Normalizer

Converts raw X posts into Story Lake entries.
Schema is immutable per TRANSFER_BRAIN_V3.
"""

def normalize_x_event(post: dict) -> dict | None:
    """
    Convert one raw X post to Story Lake schema.

    Returns:
        dict | None
    """
    text = post.get("text", "").strip()
    created_at = post.get("created_at")

    if not text or not created_at:
        return None

    headline = text.split(".")[0][:120].strip()
    summary = text[:400].strip()

    return {
        "headline": headline,
        "summary": summary,
        "domain": infer_domain(text),
        "source": "x_event",
        "semantic_keys": []
    }

def infer_domain(text: str) -> str:
    """
    Conservative domain inference. Defaults to crypto.
    """
    t = text.lower()

    if any(k in t for k in ["sec", "cftc", "regulator", "filed", "lawsuit"]):
        return "regulation"
    if any(k in t for k in ["defi", "liquidity", "tvl", "protocol", "dex"]):
        return "defi"
    if any(k in t for k in ["ai", "model", "compute", "inference"]):
        return "ai"
    if any(k in t for k in ["fed", "inflation", "rates", "macro"]):
        return "macro"

    return "crypto"

def normalize_x_events(posts: list[dict]) -> list[dict]:
    """
    Normalize multiple posts.

    Returns:
        list[dict]: Story Lake entries
    """
    out = []
    for post in posts:
        entry = normalize_x_event(post)
        if entry:
            out.append(entry)
    return out
