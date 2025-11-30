# backend/script_engine/hybrid_tone/bias_worldview.py

"""
Chip's worldview bias engine (A-17).
Subtle context lines that reflect Chip's philosophy without overwhelming analysis.
"""

def apply_worldview_bias(enriched):
    sentiment = enriched.get("sentiment", "neutral")
    domain = enriched.get("domain", "")
    importance = enriched.get("importance", 5)

    lines = []

    # ---- Market realism ----
    if domain in ["markets", "defi", "onchain"]:
        lines.append("Markets move in cycles — context matters here.")

    # ---- Regulator skepticism ----
    if domain in ["regulation", "security", "legal"]:
        lines.append("Regulation always lags the innovation curve.")

    # ---- Funding lens ----
    if domain in ["ai", "venture", "macro"]:
        lines.append("Follow the capital — funding usually signals the trend.")

    # ---- AI optimism ----
    if domain == "ai":
        lines.append("AI acceleration is still in its early innings.")

    # ---- Risk realism ----
    if importance >= 8 and sentiment == "negative":
        lines.append("Let’s stay level-headed — volatility cuts both ways.")

    # ---- Neutral catchall ----
    if not lines:
        lines.append("Always good to view this with a balanced lens.")

    # Pick ONE worldview line per story to avoid flooding
    return lines[0]
