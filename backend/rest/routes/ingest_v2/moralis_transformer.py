def format_whale_events(events):
    stories = []
    for e in events:
        token = e.get("tokenSymbol") or e.get("token")
        amount = e.get("amountUsd") or e.get("amount")
        headline = f"Whales accumulate ${amount} in {token} in the last 24 hours"
        body = f"Detected via Moralis whale API. Wallet: {e.get('wallet')}, amount: {amount}."
        stories.append({
            "headline": headline,
            "body": body,
            "source": "moralis_whales",
            "domain": "onchain",
            "importance": 6
        })
    return stories


def format_liquidations(events):
    stories = []
    total = sum([x.get("usdValue", 0) for x in events])
    headline = f"{total:,} in liquidations triggered across markets"
    body = f"{len(events)} major liquidations detected. Largest: {max(events, key=lambda x: x.get('usdValue',0))}."
    stories.append({
        "headline": headline,
        "body": body,
        "source": "moralis_liquidations",
        "domain": "markets",
        "importance": 7
    })
    return stories


def format_rpc_block(block):
    headline = f"Ethereum block {block['number']} processed with {len(block.get('transactions', []))} txns"
    body = f"Gas used: {block.get('gasUsed')} / {block.get('gasLimit')}"
    return [{
        "headline": headline,
        "body": body,
        "source": "rpc_block",
        "domain": "onchain",
        "importance": 5
    }]


def format_gas(gwei):
    headline = f"Ethereum gas spikes to {gwei} gwei"
    body = f"Mempool congestion rising. Priority fees increasing."
    return [{
        "headline": headline,
        "body": body,
        "source": "rpc_gas",
        "domain": "onchain",
        "importance": 5
    }]
