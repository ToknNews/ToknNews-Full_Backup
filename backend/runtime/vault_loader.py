#!/usr/bin/env python3
"""
vault_loader.py — Hybrid Vault + ENV loader
ToknNews 2025
"""

import os
import json
import hvac

VAULT_ADDR = os.getenv("VAULT_ADDR")
VAULT_TOKEN = os.getenv("VAULT_TOKEN")


def load_secrets():
    """
    Loads secrets from Vault.
    If Vault is unavailable or empty, falls back to environment variables.
    """

    secrets = {}

    # --- FALLBACK TO ENV FIRST ---
    # This ensures OpenAI & cluster engine DO NOT fail
    env_keys = [
        "OPENAI_API_KEY",
        "ELEVENLABS_API_KEY",
        "VAULT_ADDR",
        "VAULT_TOKEN",
    ]

    for key in env_keys:
        if os.getenv(key):
            secrets[key.lower()] = os.getenv(key)

    # --- If Vault not configured, stop here ---
    if not VAULT_ADDR or not VAULT_TOKEN:
        print("[Vault] No VAULT_TOKEN or VAULT_ADDR set — using env fallback only.")
        return secrets

    try:
        client = hvac.Client(url=VAULT_ADDR, token=VAULT_TOKEN)
        if not client.is_authenticated():
            print("[Vault] Authentication failed — using env fallback.")
            return secrets

        vault_data = client.secrets.kv.v2.read_secret_version(path="openai")
        for k, v in vault_data["data"]["data"].items():
            secrets[k.lower()] = v

        print("[Vault] Loaded secrets from Vault + env hybrid")

    except Exception as e:
        print(f"[Vault] Error loading Vault: {e} — using env fallback.")

    return secrets
