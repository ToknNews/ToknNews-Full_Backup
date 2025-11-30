#!/usr/bin/env python3
import os
import requests
from loguru import logger

# Your keys from .env
MORALIS_KEY = os.getenv("MORALIS_API_KEY")
MORALIS_SERVER = os.getenv("MORALIS_SERVER", "https://deep-index.moralis.io/api/v2")

# Speedy node endpoints (fastest available)
NODES = {
    "ethereum": f"{MORALIS_SERVER}/eth/mainnet",
    "bsc":      f"{MORALIS_SERVER}/bsc/mainnet",
    "polygon":  f"{MORALIS_SERVER}/polygon/mainnet",
    "arbitrum": f"{MORALIS_SERVER}/arbitrum/mainnet",
    "base":     f"{MORALIS_SERVER}/base/mainnet"
}

HEADERS = {
    "accept": "application/json",
    "X-API-Key": MORALIS_KEY
}

def rpc_call(chain, method, params=[]):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    try:
        r = requests.post(NODES[chain], json=payload, headers=HEADERS, timeout=8)
        return r.json().get("result")
    except Exception as e:
        logger.error(f"Moralis {chain} failed: {e}")
        return None

# TOKEN NEWS SPECIFIC HELPERS
def get_token_price(token_address, chain="ethereum"):
    return rpc_call(chain, "eth_call", [
        {"to": "0x5498BB96F5C36F4B4B1c6b3e0b5a8e8a8e8a8e8a", "data": f"0x18160ddd{token_address.lower()[2:]:064x}"}, "latest"
    ])

def get_recent_transfers(token_address, chain="ethereum", limit=20):
    return rpc_call(chain, "eth_getLogs", [{
        "address": token_address,
        "fromBlock": "latest",
        "topics": ["0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"]
    }])

def get_wallet_balance(wallet, token="0x0", chain="ethereum"):
    return rpc_call(chain, "eth_call", [
        {"to": token, "data": f"0x70a08231{wallet.lower()[2:]:064}"}, "latest"
    ])

def enrich_with_moralis(story):
    story.setdefault("moralis_context", {})
    story["moralis_context"]["timestamp"] = int(time.time())
    
    # If story mentions a token address, pull price
    if story.get("token_address"):
        price = get_token_price(story["token_address"])
        story["moralis_context"]["price"] = price
    
    # If story mentions a wallet, pull balance
    if story.get("wallet_address"):
        balance = get_wallet_balance(story["wallet_address"])
        story["moralis_context"]["balance"] = balance
    
    logger.info(f"Moralis enriched: {len(story['moralis_context'])} fields")
    return story
