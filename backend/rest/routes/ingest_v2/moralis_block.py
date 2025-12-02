MORALIS_CONTRACTS = [
    ("WETH", "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"),
    ("USDC", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606e48c"),
    ("USDT", "0xdAC17F958D2ee523a2206206994597C13D831ec7"),
    ("LINK", "0x514910771AF9Ca656af840dff83E8264EcF986CA"),
    ("WBTC", "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"),
    ("UNI",  "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984"),
]

if MORALIS_KEY:
    for symbol, address in MORALIS_CONTRACTS:
        data = safe_get(
            f"https://deep-index.moralis.io/api/v2/erc20/{address}/price?chain=eth",
            {"X-API-Key": MORALIS_KEY}
        )
        debug_api(f"Moralis-{symbol}", data)
        if data and isinstance(data, dict) and "usdPrice" in data:
            price = data["usdPrice"]
            stories.append({
                "headline": f"{symbol} price: ${price:,.2f} (Moralis)",
                "source": "Moralis"
            })
