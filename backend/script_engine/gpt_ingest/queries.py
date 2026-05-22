GPT_INGEST_QUERIES = [
    {
        "id": "capital_flow_shift",
        "purpose": "Detect meaningful capital movement narratives",
        "inputs": ["onchain"],
        "prompt_type": "flow_analysis",
        "importance_cap": 6.0
    },
    {
        "id": "exchange_behavior",
        "purpose": "Interpret exchange inflows/outflows",
        "inputs": ["onchain", "rss"],
        "prompt_type": "exchange_behavior",
        "importance_cap": 6.0
    },
    {
        "id": "liquidity_stress",
        "purpose": "Identify liquidity stress or positioning",
        "inputs": ["onchain", "rss"],
        "prompt_type": "liquidity",
        "importance_cap": 6.5
    },
    {
        "id": "macro_alignment",
        "purpose": "Check if crypto flows align with macro news",
        "inputs": ["onchain", "rss"],
        "prompt_type": "macro_context",
        "importance_cap": 5.5
    },
    {
        "id": "volatility_setup",
        "purpose": "Detect pre-volatility positioning",
        "inputs": ["onchain"],
        "prompt_type": "volatility_setup",
        "importance_cap": 6.0
    }
]
