#!/usr/bin/env python3
"""
chainstack_numeric_enricher.py

ToknNews — Multi-Chain Numeric Enrichment (Canonical v5)

Adds:
- On-chain ETH/USD pricing (Uniswap V3)
- 24h % price change via persisted daily snapshots

Persistence:
- File-based snapshots (one per chain per day)
"""

from dotenv import load_dotenv
load_dotenv("/opt/toknnews/.env")

import os
import time
import math
import json
from typing import Dict, Any
from datetime import datetime, timezone

from web3 import Web3
from web3.middleware.proof_of_authority import ExtraDataToPOAMiddleware
from backend.script_engine.onchain.uniswap_subgraph_client import fetch_uniswap_liquidity

MAX_BLOCKS_SCAN = 120

# =========================================================
# CONFIG
# =========================================================

CHAIN_RPC_ENV = {
    "ethereum": "CHAINSTACK_RPC_ETHEREUM",
    "base": "CHAINSTACK_RPC_BASE",
    "arbitrum": "CHAINSTACK_RPC_ARBITRUM",
    "monad": "CHAINSTACK_RPC_MONAD",
}

TX_WINDOW_SECONDS = 300  # 5 minutes

SNAPSHOT_DIR = "/opt/toknnews/data/numeric_snapshots"

# Canonical Uniswap V3 ETH/<stable> pools (0.05%)
UNISWAP_V3_POOLS = {
    "ethereum": Web3.to_checksum_address("0x88e6A0c2dDD26FEEb64F039a2c41296FcB3f5640"),
    "base": Web3.to_checksum_address("0x4C36388bE6F416A29C8d8Eee81C771cE6bE14B18"),
    "arbitrum": Web3.to_checksum_address("0xC6962004f452bE9203591991D15f6b388e09E8D0"),
}

UNISWAP_V3_POOL_ABI = [
    {
        "name": "slot0",
        "outputs": [
            {"name": "sqrtPriceX96", "type": "uint160"},
            {"name": "tick", "type": "int24"},
            {"name": "observationIndex", "type": "uint16"},
            {"name": "observationCardinality", "type": "uint16"},
            {"name": "observationCardinalityNext", "type": "uint16"},
            {"name": "feeProtocol", "type": "uint8"},
            {"name": "unlocked", "type": "bool"},
        ],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "token0",
        "outputs": [{"name": "", "type": "address"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "name": "token1",
        "outputs": [{"name": "", "type": "address"}],
        "inputs": [],
        "stateMutability": "view",
        "type": "function",
    },
]

ERC20_DECIMALS_ABI = [
    {"name": "decimals", "outputs": [{"type": "uint8"}], "inputs": [], "stateMutability": "view", "type": "function"}
]

# =========================================================
# HELPERS
# =========================================================

def _connect_evm(rpc_url: str) -> Web3:
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))
    if not w3.is_connected():
        raise RuntimeError(f"Failed to connect to RPC: {rpc_url}")
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    return w3


def _tx_trend(tx_count: int) -> str:
    if tx_count > 300:
        return "up"
    if tx_count < 100:
        return "down"
    return "flat"


def _read_decimals(w3: Web3, token_addr: str) -> int:
    token = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_DECIMALS_ABI)
    return int(token.functions.decimals().call())


def _eth_usd_from_uniswap_v3_pool(w3: Web3, pool_address: str) -> float:
    pool = w3.eth.contract(address=pool_address, abi=UNISWAP_V3_POOL_ABI)

    sqrt_price_x96 = pool.functions.slot0().call()[0]
    token0 = pool.functions.token0().call()
    token1 = pool.functions.token1().call()

    dec0 = _read_decimals(w3, token0)
    dec1 = _read_decimals(w3, token1)

    price_raw = (sqrt_price_x96 / (2 ** 96)) ** 2
    price_human = price_raw * (10 ** (dec0 - dec1))

    if dec0 == 18 and dec1 == 6:
        eth_usd = price_human
    elif dec0 == 6 and dec1 == 18:
        eth_usd = 1.0 / price_human
    else:
        raise RuntimeError(f"Unexpected token decimals: {dec0}, {dec1}")

    return float(eth_usd)


def _snapshot_path(chain: str, date_str: str) -> str:
    return f"{SNAPSHOT_DIR}/{chain}_{date_str}.json"


def _load_snapshot(chain: str, date_str: str) -> float | None:
    path = _snapshot_path(chain, date_str)
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return float(json.load(f)["price_usd"])


def _save_snapshot(chain: str, date_str: str, price_usd: float) -> None:
    path = _snapshot_path(chain, date_str)
    if os.path.exists(path):
        return
    with open(path, "w") as f:
        json.dump({"price_usd": price_usd}, f)


def _compute_24h_change(chain: str, current_price: float) -> float | None:
    today = datetime.now(timezone.utc).date()
    yesterday = today.replace(day=today.day - 1)

    prev_price = _load_snapshot(chain, yesterday.isoformat())
    if prev_price is None:
        return None

    return round(((current_price - prev_price) / prev_price) * 100, 2)

# =========================================================
# PER-CHAIN FETCHERS
# =========================================================

def _fetch_evm_chain(chain: str, rpc_url: str) -> Dict[str, Any]:
    w3 = _connect_evm(rpc_url)

    latest_block = w3.eth.block_number
    now_ts = int(time.time())
    cutoff_ts = now_ts - TX_WINDOW_SECONDS

    tx_count_5m = 0
    block_cursor = latest_block

    blocks_scanned = 0

    while block_cursor >= 0 and blocks_scanned < MAX_BLOCKS_SCAN:
        blk = w3.eth.get_block(block_cursor, full_transactions=False)
        if blk.timestamp < cutoff_ts:
            break
        tx_count_5m += len(blk.transactions)
        block_cursor -= 1
        blocks_scanned += 1

    price_usd = None
    price_source = None
    change_24h = None

    pool = UNISWAP_V3_POOLS.get(chain)
    if pool:
        price_usd = _eth_usd_from_uniswap_v3_pool(w3, pool)
        price_source = "dex"

        today_str = datetime.now(timezone.utc).date().isoformat()
        _save_snapshot(chain, today_str, price_usd)
        change_24h = _compute_24h_change(chain, price_usd)

    return {
        "chain": chain,
        "native_symbol": "ETH",
        "price": {
            "usd": price_usd,
            "change_24h_pct": change_24h,
            "source": price_source,
        },
        "activity": {
            "latest_block": latest_block,
            "tx_count_5m": tx_count_5m,
            "tx_trend": _tx_trend(tx_count_5m),
        },
        "liquidity": {},
        "signals": {},
    }

# =========================================================
# MAIN ORCHESTRATOR
# =========================================================

def generate_numeric_enrichment() -> Dict[str, Any]:
    """
    Generate canonical numeric enrichment across all configured chains.

    Behavior:
    - Attempts each chain independently
    - Fails soft per chain
    - Logs warnings instead of silently skipping
    - Always returns a valid structure
    """

    result: Dict[str, Any] = {
        "timestamp": int(time.time()),
        "chains": {}
    }

    # Ensure snapshot persistence path exists
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)

    for chain, env_key in CHAIN_RPC_ENV.items():
        rpc_url = os.getenv(env_key)

        if not rpc_url:
            print(f"[NUMERIC][INFO] {chain} skipped (no RPC URL in env)")
            continue

        try:
            chain_data = _fetch_evm_chain(chain, rpc_url)

            # Defensive sanity check
            if not isinstance(chain_data, dict):
                raise RuntimeError("invalid chain data returned")

            result["chains"][chain] = chain_data

        except Exception as e:
            # Explicit logging, fail-soft
            print(f"[NUMERIC][WARN] {chain} skipped due to error: {e}")
            continue

    return result

# =========================================================
# CLI ENTRYPOINT
# =========================================================

if __name__ == "__main__":
    print(json.dumps(generate_numeric_enrichment(), indent=2))
