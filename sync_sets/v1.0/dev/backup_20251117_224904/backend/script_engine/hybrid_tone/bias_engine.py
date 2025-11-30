# hybrid_tone/bias_engine.py
"""
A-13 — Chip Blue Worldview Bias Layer (v1)
Adds subtle interpretive bias to Chip's commentary.
"""

def compute_chip_bias(enriched):
    """
    Returns a short bias phrase Chip injects into his commentary.
    """
    sentiment = enriched.get("sentiment", "neutral")
    domain = enriched.get("domain", "general")
    importance = enriched.get("importance", 5)

    # --- Macro worldview biases ---
    macro_bias = {
        "markets": "from a broader macro lens",
        "defi": "considering how fast DeFi moves",
        "ai": "given the pace of AI acceleration",
        "security": "and that raises real security concerns",
        "regulation": "as Washington continues dragging its feet",
        "venture": "in the context of shifting capital appetite",
    }

    # Pick domain-based bias
    domain_phrase = macro_bias.get(domain.lower(), "")

    # --- Sentiment-based overlays ---
    if sentiment == "negative":
        senti_phrase = "and frankly, this trend is worrying"
    elif sentiment == "positive":
        senti_phrase = "and this could be more meaningful than it looks"
    else:
        senti_phrase = "and it’s worth watching where this goes"

    # --- Severity trigger ---
    if importance >= 8:
        severity = "— especially at this scale"
    else:
        severity = ""

    # Build final bias
    parts = [domain_phrase, senti_phrase, severity]
    parts = [p for p in parts if p]

    if not parts:
        return ""

    return " ".join(parts)
