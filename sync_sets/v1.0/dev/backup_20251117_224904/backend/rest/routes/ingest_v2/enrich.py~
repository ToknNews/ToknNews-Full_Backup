from fastapi import APIRouter
from pydantic import BaseModel
import os, json, time
from openai import OpenAI

router = APIRouter(prefix="/ingest/v2")
client = OpenAI()

# Canonical domains mapped to primary anchors
PRIMARY_ROUTING = {
    "breaking": "Chip Blue",
    "markets": "Cash Green",
    "macro": "Bond Crimson",
    "volatility": "Rex Vol",
    "onchain": "Ledger Stone",
    "legal": "Lawson Black",
    "defi": "Reef Gold",
    "ai": "Neura Grey",
    "ethics": "Ivy Quinn",
    "venture": "Cap Silver",
    "culture": "Bitsy Gold",
    "retail": "Penny Lane",
    "nightline": "Rex Vol"
}

ALL_CHARACTERS = list(set(PRIMARY_ROUTING.values()))

# Chip Blue's bias profile (locked as user-requested)
CHIP_BIAS = {
    "crypto_bullish": True,
    "ai_optimistic": True,
    "meme_skeptical": True,
    "regulator_distrust": True,
    "risk": "moderate",
    "professional": True,
    "funny_deadpan": True
}

class Item(BaseModel):
    id: str
    headline: str
    url: str
    source: str
    ts: float

DOMAIN_PROMPT = """
Classify the headline into EXACTLY ONE of the following domains:

breaking, markets, macro, volatility, onchain, legal, defi,
ai, ethics, venture, culture, retail, nightline

Return as JSON: {"domain": "<one>"}
"""

BASE_ANALYSIS_PROMPT = """
Return JSON ONLY with:

{
    "category": "",
    "sentiment": "",
    "importance": 0,
    "summary": ""
}
"""

CHIP_REACTION_PROMPT = """
Chip Blue is the lead ToknNews anchor.

Chip’s bias model:
- moderately bullish crypto
- very optimistic on AI
- cautious on meme coins
- skeptical of hype cycles
- distrustful of regulators
- professional but dryly witty
- moderate risk tolerance

Given the headline and summary, return Chip’s natural reaction in JSON:

{
 "chip_reaction": "",
 "chip_tone": "",
 "chip_quip": ""
}
"""

def classify_domain(headline: str):
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": DOMAIN_PROMPT + f"\nHeadline: {headline}"}],
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)["domain"]

def run_base_analysis(headline: str):
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": f"Headline: {headline}\n{BASE_ANALYSIS_PROMPT}"}],
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)

def chip_should_appear(domain: str, importance: int):
    # CHIP decides whether he's working this story
    serious = ["breaking", "macro", "legal", "ai"]
    if domain in serious:
        return True
    if importance >= 60:
        return True
    return False  # light stories handled by desk anchors

def determine_primary_secondary(domain: str, headline: str):
    h = headline.lower()

    # overrides for primary
    if any(x in h for x in ["sec", "ruling", "lawsuit", "regulator"]):
        return ("Lawson Black", None)

    if any(x in h for x in ["raises", "series", "funding", "startup"]):
        return ("Cap Silver", "Neura Grey")  # AI startup? Cap leads.

    if any(x in h for x in ["staking", "apy", "yield", "liquidity"]):
        return ("Reef Gold", "Cash Green")

    if any(x in h for x in ["ai", "llm", "model", "neural"]):
        # If it's AI funding → Cap primary, Neura secondary
        if any(y in h for y in ["raises", "funding"]):
            return ("Cap Silver", "Neura Grey")
        return ("Neura Grey", None)

    if any(x in h for x in ["meme", "trend", "viral"]):
        return ("Bitsy Gold", "Rex Vol")

    # fallback domain mapping
    primary = PRIMARY_ROUTING.get(domain, "Chip Blue")
    return (primary, None)

def get_chip_reaction(headline: str, summary: str):
    payload = f"Headline: {headline}\nSummary: {summary}\n{CHIP_REACTION_PROMPT}"
    resp = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": payload}],
        response_format={"type": "json_object"}
    )
    return json.loads(resp.choices[0].message.content)

@router.post("/enrich")
def enrich_item(item: Item):

    # Step 1: Base analysis (sentiment, summary, importance)
    base = run_base_analysis(item.headline)

    # Step 2: Domain
    domain = classify_domain(item.headline)

    # Step 3: Assign primary and secondary anchors
    primary, secondary = determine_primary_secondary(domain, item.headline)

    # Step 4: Decide if Chip participates
    chip_involved = chip_should_appear(domain, base["importance"])

    chip_data = None
    if chip_involved:
        chip_data = get_chip_reaction(item.headline, base["summary"])

    enriched = {
        "id": item.id,
        "headline": item.headline,
        "url": item.url,
        "source": item.source,
        "ts": item.ts,
        "category": base["category"],
        "sentiment": base["sentiment"],
        "importance": base["importance"],
        "summary": base["summary"],
        "domain": domain,
        "primary_character": primary,
        "secondary_character": secondary,
        "chip_involved": chip_involved,
        "chip_reaction": chip_data["chip_reaction"] if chip_data else None,
        "chip_tone": chip_data["chip_tone"] if chip_data else None,
        "chip_quip": chip_data["chip_quip"] if chip_data else None,
        "reason_primary": f"Primary chosen by domain='{domain}' and headline cues.",
        "reason_secondary": f"Secondary chosen by nuance in headline." if secondary else None
    }

    return enriched
