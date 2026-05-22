#!/usr/bin/env python3
"""
chainstack_agent.py

ToknNews — On-Chain Intelligence Agent (RPC-Level)

PURPOSE:
- Connect to Chainstack-managed RPC
- Fetch precise on-chain data (blocks, balances, events)
- Structure data for AI analysis
- Output machine-readable artifacts for verticals

DESIGN:
- Deterministic RPC → structured data → optional AI analysis
- Does NOT replace Moralis
- Complements existing ingestion

SUPPORTED:
- Ethereum Mainnet (default)
- Easily extendable to Base / others
"""

from dotenv import load_dotenv
load_dotenv("/opt/toknnews/.env")

import os
import time
import json
import logging
from typing import Dict, Any, List, Optional

from web3 import Web3
from web3.middleware import geth_poa_middleware
import openai

# -----------------------------------------------------
# CONFIG
# -----------------------------------------------------

CHAINSTACK_RPC_URL = os.getenv("CHAINSTACK_RPC_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not CHAINSTACK_RPC_URL:
    raise RuntimeError("Missing CHAINSTACK_RPC_URL")

if not OPENAI_API_KEY:
    raise RuntimeError("Missing OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [CHAINSTACK] %(levelname)s: %(message)s"
)

# -----------------------------------------------------
# RPC CLIENT
# -----------------------------------------------------

class ChainstackClient:
    def __init__(self, rpc_url: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
        if not self.w3.is_connected():
            raise RuntimeError("Failed to connect to Chainstack RPC")

        # Enable POA middleware for chains like Base if needed later
        self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)

        logging.info("Connected to Chainstack RPC")

    # -----------------------------
    # BASIC CHAIN DATA
    # -----------------------------

    def latest_block(self) -> Dict[str, Any]:
        block = self.w3.eth.get_block("latest", full_transactions=False)
        return {
            "number": block.number,
            "timestamp": block.timestamp,
            "tx_count": len(block.transactions),
        }

    def wallet_balance(self, address: str) -> float:
        wei = self.w3.eth.get_balance(self.w3.to_checksum_address(address))
        return float(self.w3.from_wei(wei, "ether"))

    # -----------------------------
    # EVENT LOG FETCHING
    # -----------------------------

    def fetch_logs(
        self,
        address: Optional[str],
        topics: Optional[List[str]],
        from_block: int,
        to_block: int,
    ) -> List[Dict[str, Any]]:
        logs = self.w3.eth.get_logs({
            "fromBlock": from_block,
            "toBlock": to_block,
            "address": address,
            "topics": topics,
        })
        return [dict(log) for log in logs]


# -----------------------------------------------------
# AI ANALYSIS AGENT
# -----------------------------------------------------

class OnChainAIAgent:
    """
    Takes structured on-chain data and produces
    analysis suitable for verticals.
    """

    def analyze(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
You are an on-chain crypto analyst.

DATA:
{json.dumps(payload, indent=2)}

TASK:
- Detect unusual activity
- Identify potential accumulation or distribution
- Flag possible alerts
- Return ONLY JSON

FORMAT:
{{
  "signal": "bullish | bearish | neutral",
  "confidence": 0.0-1.0,
  "notes": "brief explanation",
  "alert": true | false
}}
"""

        rsp = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300,
        )

        return json.loads(rsp.choices[0].message.content)


# -----------------------------------------------------
# MAIN ORCHESTRATOR
# -----------------------------------------------------

class ChainstackAgent:
    def __init__(self):
        self.client = ChainstackClient(CHAINSTACK_RPC_URL)
        self.ai = OnChainAIAgent()

    def run(self) -> Dict[str, Any]:
        """
        Example run loop:
        - Fetch latest block
        - Analyze for signals
        """

        block = self.client.latest_block()

        payload = {
            "chain": "ethereum",
            "latest_block": block,
            "observed_at": int(time.time()),
        }

        analysis = self.ai.analyze(payload)

        return {
            "raw": payload,
            "analysis": analysis,
        }


# -----------------------------------------------------
# CLI ENTRYPOINT (FOR TESTING)
# -----------------------------------------------------

if __name__ == "__main__":
    agent = ChainstackAgent()
    result = agent.run()
    print(json.dumps(result, indent=2))
