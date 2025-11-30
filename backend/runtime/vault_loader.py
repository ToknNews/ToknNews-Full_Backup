#!/usr/bin/env python3
"""
Unified secret accessor for ToknNews.
Uses Vault if available, otherwise ENV fallback.
"""

import os
import requests

VAULT_ADDR = os.getenv("VAULT_ADDR", "http://127.0.0.1:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")
SECRET_PATH = "secret/data/toknnews/ingestion"


def load_secrets():
    """Load from Vault with ENV fallback."""
    # No Vault token → fallback
    if not VAULT_TOKEN:
        print("[Vault] No VAULT_TOKEN, using ENV fallback.")
        return _env()

    try:
        url = f"{VAULT_ADDR}/v1/{SECRET_PATH}"
        resp = requests.get(url, headers={"X-Vault-Token": VAULT_TOKEN}, timeout=3)

        if resp.status_code != 200:
            print(f"[Vault] ({resp.status_code}) fallback to ENV.")
            return _env()

        data = resp.json().get("data", {}).get("data", {})
        merged = {**_env(), **data}
        return merged

    except Exception as e:
        print(f"[Vault] ERROR: {e}")
        return _env()


def _env():
    """ENV fallback."""
    return {
        "marketaux_api_key": os.getenv("MARKETAUX_API_KEY", ""),
        "newsdata_api_key": os.getenv("NEWSDATA_API_KEY", ""),
        "cryptopanic_key": os.getenv("CRYPTOPANIC_KEY", ""),
        "moralis_api_key": os.getenv("MORALIS_API_KEY", ""),
        "openai_api_key": os.getenv("OPENAI_API_KEY", ""),
        "rpc_mainnet": os.getenv("RPC_MAINNET", "https://eth.llamarpc.com"),
    }
