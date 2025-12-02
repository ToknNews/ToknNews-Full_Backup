#!/usr/bin/env python3
# /opt/toknnews/backend/live/add_contract.py

import os
import sys
import json
import shutil
from pathlib import Path

CONFIG_PATH = Path("/opt/toknnews/config/contracts.json")
VALID_CHAINS = {"eth", "bsc", "polygon"}
VALID_TYPES = {"erc20", "nft721", "nft1155"}

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return json.load(f)

def save_config(data):
    backup_path = CONFIG_PATH.with_suffix(".json.bak")
    shutil.copy(CONFIG_PATH, backup_path)
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"[✓] Contract added. Backup saved to {backup_path}")

def add_contract(chain, category, address):
    chain = chain.lower()
    category = category.lower()
    address = address.lower()

    if chain not in VALID_CHAINS:
        print(f"[!] Invalid chain: {chain}")
        return
    if category not in VALID_TYPES:
        print(f"[!] Invalid type: {category}")
        return

    config = load_config()

    if address in config.get(chain, {}).get(category, []):
        print("[!] Address already exists in config.")
        return

    config.setdefault(chain, {}).setdefault(category, []).append(address)
    save_config(config)

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 add_contract.py <chain> <erc20|nft721|nft1155> <contract_address>")
        sys.exit(1)
    _, chain, category, address = sys.argv
    add_contract(chain, category, address)
