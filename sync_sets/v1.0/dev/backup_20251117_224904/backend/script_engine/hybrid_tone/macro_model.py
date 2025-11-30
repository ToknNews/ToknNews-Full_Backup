# backend/script_engine/hybrid_tone/macro_model.py

def compute_macro_context(enriched):
    """
    Returns a macro-context line based on domain + sentiment + importance.
    This runs BEFORE Chip’s bias injection, AFTER tone shaping.
    """

    domain = enriched.get("domain", "").lower()
    sentiment = enriched.get("sentiment", "neutral").lower()
    importance = enriched.get("importance", 5)

    # ---- Risk-on signals ----
    risk_on_domains = ["ai", "tech", "venture", "markets"]
    if domain in risk_on_domains and sentiment == "positive":
        return "Broadly, this leans risk-on — liquidity tends to favor moves like this."

    # ---- Risk-off signals ----
    risk_off_domains = ["security", "regulation", "legal"]
    if domain in risk_off_domains and sentiment == "negative":
        return "Bigger picture, this pushes things risk-off — caution tends to dominate here."

    # ---- Liquidity conditions ----
    if domain == "markets":
        if importance >= 8:
            return "From a liquidity standpoint, this kind of move usually reflects deeper structural pressure."
        else:
            return "Liquidity-wise, this is notable but not system-level."

    # ---- On-chain context ----
    if domain in ["onchain", "defi"]:
        if sentiment == "negative":
            return "On-chain, signals like this usually point to stress building under the surface."
        else:
            return "On-chain flows generally support this direction in the near term."

    # Default: no macro context
    return ""
