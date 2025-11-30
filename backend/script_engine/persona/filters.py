import re

# Only allow English + crypto/finance/tech keywords
ENGLISH_CRYPTO_KEYWORDS = [
    "bitcoin", "btc", "ethereum", "eth", "solana", "defi", "yield", "liquidity", "amm", "lp",
    "nft", "opensea", "blur", "sec", "regulation", "gary gensler", "etf", "blackrock", "fidelity",
    "coinbase", "binance", "kraken", "gemini", "bybit", "okx", "whale", "wallet", "on-chain",
    "hack", "breach", "exploit", "rug", "pump", "dump", "fomo", "fud", "rekt", "alpha", "beta",
    "stablecoin", "usdt", "usdc", "dai", "lido", "aave", "compound", "curve", "uniswap", "sushi",
    "fed", "powell", "cpi", "inflation", "rates", "treasury", "yield curve", "recession", "bull", "bear"
]

def is_english_crypto_headline(headline: str) -> bool:
    headline_lower = headline.lower()

    # Must contain at least one crypto/finance keyword
    if not any(k in headline_lower for k in ENGLISH_CRYPTO_KEYWORDS):
        return False

    # Block obvious non-English (French, Korean, Arabic, etc.)
    if re.search(r'[àâäéèêëîïôöùûüçœ]', headline_lower):
        return False
    if re.search(r'[가-힣]', headline_lower):  # Korean
        return False
    if re.search(r'[а-яё]', headline_lower):  # Russian
        return False
    if re.search(r'[أ-ي]', headline_lower):   # Arabic
        return False

    # Must be mostly ASCII (English)
    if len(re.findall(r'[a-zA-Z0-9\s\.\,\!\?\$\%\-\_]', headline)) / len(headline) < 0.8:
        return False

    return True
