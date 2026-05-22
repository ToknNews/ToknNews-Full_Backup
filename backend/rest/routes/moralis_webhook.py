from flask import Blueprint, request, Response
import json
import time
from pathlib import Path
import os

MORALIS_ENABLED = os.getenv("MORALIS_ENABLED", "false").lower() == "true"

moralis_webhook = Blueprint("moralis_webhook", __name__)

STORY_LAKE_PATH = Path("/opt/toknnews/data/stories/story_lake.json")
STORY_LAKE_PATH.parent.mkdir(parents=True, exist_ok=True)

USD_THRESHOLD = 1_000_000  # $1M minimum signal

# --------------------------------------------------
# EXCHANGE ADDRESS TAGGING (PARTIAL LIST)
# --------------------------------------------------

EXCHANGE_WALLETS = {
    # Binance
    "0x28c6c06298d514db089934071355e5743bf21d60": "Binance",
    "0xdfd5293d8e347dfe59e90efd55b2956a1343963d": "Binance",

    # Coinbase
    "0x503828976d22510aad0201ac7ec88293211d23da": "Coinbase",
    "0x71660c4005ba85c37ccec55d0c4493e66fe775d3": "Coinbase",

    # OKX
    "0x8894e0a0c962cb723c1976a4421c95949be2d4e3": "OKX",

    # Kraken
    "0x267be1c1d684f78cb4f6a176c4911b741e4ffdc0": "Kraken",

    # Bitfinex
    "0x742d35cc6634c0532925a3b844bc454e4438f44e": "Bitfinex",
}

def tag_exchange(address: str | None) -> str | None:
    if not address:
        return None
    return EXCHANGE_WALLETS.get(address.lower())

def load_story_lake():
    if STORY_LAKE_PATH.exists():
        try:
            return json.loads(STORY_LAKE_PATH.read_text())
        except Exception:
            return []
    return []

def append_story(item):
    stories = load_story_lake()
    stories.append(item)
    STORY_LAKE_PATH.write_text(json.dumps(stories, indent=2))

def chain_name(chain_id: str) -> str:
    return {
        "0x1": "ethereum",
        "0x2105": "base",
        "0xa4b1": "arbitrum",
    }.get(chain_id.lower(), "unknown")

@moralis_webhook.route("/webhook/moralis", methods=["POST"])
def handle_moralis_webhook():
    """
    Moralis ERC-20 webhook handler (batched upgrades):
    - Robust payload parsing
    - Exchange tagging
    - TX hash deduplication
    - Bridge / L2 flow detection
    - Stablecoin importance weighting
    - ALWAYS returns empty 200
    """

    if not MORALIS_ENABLED:
        return Response(status=200)

    payload = request.get_json(silent=True)
    if not payload or payload.get("confirmed") is not True:
        return Response(status=200)

    chain = chain_name(payload.get("chainId"))

    # --------------------------------------------------
    # COLLECT ERC20 TRANSFERS (ROBUST TO PAYLOAD SHAPES)
    # --------------------------------------------------
    transfers = []

    if isinstance(payload.get("erc20Transfers"), list):
        transfers = payload["erc20Transfers"]
    elif isinstance(payload.get("txs"), list):
        for tx in payload["txs"]:
            if isinstance(tx.get("erc20Transfers"), list):
                transfers.extend(tx["erc20Transfers"])

    if not transfers:
        return Response(status=200)

    # --------------------------------------------------
    # LOAD STORY LAKE ONCE (FOR DEDUPE)
    # --------------------------------------------------
    try:
        existing = load_story_lake()
        seen_hashes = {s.get("tx_hash") for s in existing if s.get("tx_hash")}
    except Exception:
        seen_hashes = set()

    # --------------------------------------------------
    # PROCESS TRANSFERS
    # --------------------------------------------------
    for transfer in transfers:
        try:
            tx_hash = transfer.get("transactionHash")
            if not tx_hash or tx_hash in seen_hashes:
                continue

            value_usd = float(transfer.get("valueUsd") or 0)
            if value_usd < USD_THRESHOLD:
                continue

            token = transfer.get("tokenSymbol", "UNKNOWN")
            from_addr = transfer.get("from")
            to_addr = transfer.get("to")

            from_exchange = tag_exchange(from_addr)
            to_exchange = tag_exchange(to_addr)

            # --------------------------------------------------
            # BRIDGE / L2 FLOW DETECTION
            # --------------------------------------------------
            bridge_flow = None
            if chain == "ethereum":
                bridge_flow = "L1 → L2"
            elif chain in ("base", "arbitrum"):
                bridge_flow = "L2 activity"

            # --------------------------------------------------
            # STABLECOIN WEIGHTING
            # --------------------------------------------------
            is_stablecoin = token.upper() in ("USDC", "USDT", "DAI")
            importance = round(value_usd / (3_000_000 if is_stablecoin else 5_000_000), 2)
            importance = min(10.0, importance)

            # --------------------------------------------------
            # HEADLINE LOGIC
            # --------------------------------------------------
            if from_exchange and not to_exchange:
                headline = f"${value_usd:,.0f} {token} withdrawn from {from_exchange}"
            elif not from_exchange and to_exchange:
                headline = f"${value_usd:,.0f} {token} deposited to {to_exchange}"
            elif from_exchange and to_exchange:
                headline = f"${value_usd:,.0f} {token} moved from {from_exchange} to {to_exchange}"
            elif bridge_flow:
                headline = f"${value_usd:,.0f} {token} {bridge_flow} transfer"
            else:
                headline = f"${value_usd:,.0f} {token} on-chain transfer detected"

            summary = (
                f"${value_usd:,.2f} {token} transferred from {from_addr} "
                f"to {to_addr} on {chain}"
            )

            story = {
                "headline": headline,
                "summary": summary,
                "domain": "onchain",
                "sentiment": "Neutral",
                "importance": importance,
                "anchors": ["ledger"],
                "source": "moralis_stream",
                "timestamp": time.time(),
                "chain": chain,
                "tx_hash": tx_hash,
                "token": token,
                "value_usd": value_usd,
                "from": from_addr,
                "to": to_addr,
                "from_exchange": from_exchange,
                "to_exchange": to_exchange,
                "bridge_flow": bridge_flow,
                "raw_onchain": transfer,
            }

            append_story(story)
            seen_hashes.add(tx_hash)

        except Exception:
            continue

    return Response(status=200)

