#!/usr/bin/env python3
"""
create_moralis_stream.py
ToknNews — Moralis Stream Creation via REST API

Creates and configures a Moralis Stream without SDKs.
"""

import os
import json
import requests

# ==================================================
# CONFIG
# ==================================================

MORALIS_API_KEY = os.getenv("MORALIS_API_KEY")
if not MORALIS_API_KEY:
    raise RuntimeError("MORALIS_API_KEY not set")

WEBHOOK_URL = "https://toknnews.com/webhook/moralis"
DESCRIPTION = "ToknNews On-Chain Large Stablecoin Transfers"
TAG = "toknnews_onchain_v1"

CHAINS = [
    "0x1",        # Ethereum
    "0x2105",     # Base
    "0xa4b1",     # Arbitrum
    "0x27bc",     # Monad
    "0x4268",     # HyperEVM
]

ERC20_TRANSFER_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    }
]

HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "X-API-Key": MORALIS_API_KEY,
}

BASE_URL = "https://api.moralis.io/streams/evm"

# ==================================================
# STEP 1 — CREATE STREAM
# ==================================================

create_payload = {
    "webhookUrl": WEBHOOK_URL,
    "description": DESCRIPTION,
    "tag": TAG,
    "chains": CHAINS,
    "includeNativeTxs": False,
    "includeInternalTxs": False,
    "includeContractLogs": False,
}

print("[*] Creating Moralis stream…")
resp = requests.post(BASE_URL, headers=HEADERS, json=create_payload)
resp.raise_for_status()

stream = resp.json()
stream_id = stream["id"]

print(f"[OK] Stream created: {stream_id}")

# ==================================================
# STEP 2 — UPDATE STREAM WITH ERC20 TRANSFER ABI
# ==================================================

update_payload = {
    "description": DESCRIPTION + " (ERC20 Transfer)",
    "abi": ERC20_TRANSFER_ABI,
    "topic0": ["Transfer(address,address,uint256)"],
    "includeContractLogs": True,
}

print("[*] Updating stream with ERC20 Transfer ABI…")
resp = requests.put(f"{BASE_URL}/{stream_id}", headers=HEADERS, json=update_payload)
resp.raise_for_status()

print("[OK] Stream updated with ERC20 Transfer ABI")
print(f"[DONE] Stream ID: {stream_id}")
