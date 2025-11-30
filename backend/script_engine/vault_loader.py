#!/usr/bin/env python3
"""
vault_loader.py — single source of truth for all secrets
Loads from HashiCorp Vault → falls back to .env
"""

import os
import hvac
from script_engine.utils import log

def load_secrets():
    # Try Vault first
    client = hvac.Client(url=os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200'))
    
    token = os.getenv('VAULT_TOKEN')
    if not token and os.path.exists('/home/ubuntu/.vault-token'):
        with open('/home/ubuntu/.vault-token') as f:
            token = f.read().strip()
    
    if token:
        client.token = token
    
    if token and client.is_authenticated():
        try:
            data = client.secrets.kv.v2.read_secret_version(path='secret/data/toknnews')['data']['data']
            for k, v in data.items():
                os.environ[k] = str(v)
            log("[VAULT] Secrets loaded from HashiCorp Vault")
            return
        except Exception as e:
            log(f"[VAULT] Failed: {e} → falling back to .env")
    
    # Fallback to .env
    from dotenv import load_dotenv
    load_dotenv("/opt/toknnews/.env")
    log("[VAULT] Secrets loaded from .env (fallback)")

# Auto-run on import
load_secrets()
