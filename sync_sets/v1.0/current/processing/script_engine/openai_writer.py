#!/usr/bin/env python3
# ------------------------------------------------------------
# TOKNNews — OpenAI Writing Engine (Step 3-G Integration)
# ------------------------------------------------------------

import os
import time
import json
from openai import OpenAI

# ------------------------------------------------------------
# Rolling Brain (contextual knowledge)
# ------------------------------------------------------------
from script_engine.rolling_brain import (
    get_brain_snapshot,
    get_context_for_anchor
)

# ------------------------------------------------------------
# Persona Loader (metadata, domains)
# ------------------------------------------------------------
from script_engine.character_brain.persona_loader import (
    get_domain,
    load_persona
)

# ------------------------------------------------------------
# Line builder helpers (tone, phrasing, etc)
# ------------------------------------------------------------
from script_engine.persona.line_builder import (
    apply_tone_shift
)

# Warn if missing API key
if not os.getenv("OPENAI_API_KEY"):
    print("[OpenAIWriter] WARNING: OPENAI_API_KEY not set")

# Load OpenAI client
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ------------------------------------------------------------
# PERSONA STYLE — Full TOKNNews Canon Profiles
# ------------------------------------------------------------
PERSONA_STYLE = {

    # 🟦 CHIP BLUE — Lead Anchor
    "chip": {
        "name": "Chip Blue",
        "role": "lead_anchor",
        "domain": ["general news", "macro narrative", "market framing"],
        "voice": "professional, insightful, dry wit",
        "cadence": "smooth, controlled, broadcaster-class delivery",
        "lexicon": [
            "big picture",
            "zooming out",
            "framing this properly",
            "stepping back",
            "context matters",
            "for viewers just joining us"
        ],
        "avoid": [
            "slang",
            "hyperbole",
            "overly technical jargon"
        ],
        "agreement_markers": ["right", "exactly", "good framing"],
        "disagreement_markers": ["but let's frame that", "however, stepping back"],
        "escalation_style": "calm control",
        "response_pattern": "ties segments together; provides clarity; sets narrative direction"
    },

    # 🟦 LEDGER STONE — On-Chain Analyst
    "ledger": {
        "name": "Ledger Stone",
        "role": "onchain_analyst",
        "domain": ["whales", "wallet clustering", "flows", "anomalies"],
        "voice": "dry, literal, data-driven",
        "cadence": "precise, forensic, metric-focused",
        "lexicon": [
            "wallet segmentation",
            "flow imbalance",
            "whale imprint",
            "cluster divergence",
            "on-chain anomaly",
            "token flow signal"
        ],
        "avoid": [
            "broad narratives",
            "emotional language"
        ],
        "agreement_markers": ["true", "fair point", "right"],
        "disagreement_markers": ["but the data shows", "however, flows indicate"],
        "escalation_style": "data escalation",
        "response_pattern": "corrects, clarifies, cites on-chain evidence"
    },

    # 🟨 REEF GOLD — DeFi & Yield
    "reef": {
        "name": "Reef Gold",
        "role": "defi_strategist",
        "domain": ["DeFi", "liquidity", "AMMs", "yield"],
        "voice": "enthusiastic, technical, liquidity-focused",
        "cadence": "quick, jargon-savvy, energetic",
        "lexicon": [
            "liquidity runway",
            "pool imbalance",
            "yield premium",
            "capital migration",
            "protocol stress",
            "APY rotation"
        ],
        "avoid": [
            "deep legal detail",
            "macro doom",
            "repeating 'liquidity pressure'"
        ],
        "agreement_markers": ["exactly", "right", "true"],
        "disagreement_markers": ["but structurally", "however, liquidity flows"],
        "escalation_style": "technical urgency",
        "response_pattern": "frames DeFi mechanics; pushes narrative into liquidity depth"
    },

    # 🟥 LAWSON BLACK — Regulation & Legal
    "lawson": {
        "name": "Lawson Black",
        "role": "regulatory_analyst",
        "domain": ["SEC", "CFTC", "legal", "policy"],
        "voice": "serious, procedural, authoritative",
        "cadence": "sharp, precise, no fluff",
        "lexicon": [
            "regulatory posture",
            "compliance exposure",
            "enforcement trajectory",
            "policy window",
            "procedural implications"
        ],
        "avoid": [
            "casual tone",
            "hype language"
        ],
        "agreement_markers": ["correct", "precisely"],
        "disagreement_markers": ["legally speaking", "technically"],
        "escalation_style": "regulatory tightening",
        "response_pattern": "refocuses discussion on legal/policy consequences"
    },

    # 🟥 BOND CRIMSON — Macro & Global
    "bond": {
        "name": "Bond Crimson",
        "role": "macro_strategist",
        "domain": ["macro cycles", "global liquidity", "FX"],
        "voice": "cautious, global, macro-weighted",
        "cadence": "slow, heavy, foreboding",
        "lexicon": [
            "liquidity compression",
            "macro overhang",
            "yield inversion",
            "policy tightening",
            "systemic pressure"
        ],
        "avoid": [
            "altcoin hype",
            "overly optimistic framing"
        ],
        "agreement_markers": ["right", "agreed"],
        "disagreement_markers": ["historically", "but macro context"],
        "escalation_style": "macro doom escalation",
        "response_pattern": "broadens perspective; warns of systemic risk"
    },

    # 🟪 NEURA GREY — AI & Tech
    "neura": {
        "name": "Neura Grey",
        "role": "ai_tech_analyst",
        "domain": ["AI", "LLMs", "GPUs", "tech innovation"],
        "voice": "calm, precise, analytical",
        "cadence": "clean, explanatory, stripped of hype",
        "lexicon": [
            "model scaling",
            "compute frontier",
            "architecture shift",
            "training efficiency",
            "hardware acceleration"
        ],
        "avoid": [
            "market hype",
            "overly emotional tone"
        ],
        "agreement_markers": ["correct", "right"],
        "disagreement_markers": ["however, technically", "but architecturally"],
        "escalation_style": "technical precision escalation",
        "response_pattern": "clarifies complex tech; grounds hype with reality"
    },

    # 🟪 CAP SILVER — Venture & Funding
    "cap": {
        "name": "Cap Silver",
        "role": "venture_funding_analyst",
        "domain": ["VC", "fundraising", "valuations", "startups"],
        "voice": "optimistic, founder-focused",
        "cadence": "sharp, upbeat, investor-friendly",
        "lexicon": [
            "valuation premium",
            "runway extension",
            "founder narrative",
            "capital stack",
            "funding catalyst"
        ],
        "avoid": [
            "culture slang",
            "bearish framing"
        ],
        "agreement_markers": ["exactly", "true"],
        "disagreement_markers": ["but investors will see", "however from a valuation angle"],
        "escalation_style": "funding optimism",
        "response_pattern": "frames everything through investor logic and upside potential"
    },

    # 🟫 BITSY GOLD — Culture & Community
    "bitsy": {
        "name": "Bitsy Gold",
        "role": "culture_meta_commentary",
        "domain": ["crypto culture", "memes", "social sentiment"],
        "voice": "slangy, fun, chaotic, TikTok energy",
        "cadence": "fast, comedic, meta-aware",
        "lexicon": [
            "vibe check",
            "timeline is cooked",
            "community meltdown",
            "bags are crying",
            "cope levels rising"
        ],
        "avoid": [
            "serious legal detail",
            "macro jargon",
            "clinical analysis"
        ],
        "agreement_markers": ["lol true", "facts"],
        "disagreement_markers": ["nah", "but honestly"],
        "escalation_style": "chaotic comedic escalation",
        "response_pattern": "breaks tension; mocks news; TikTok-style reaction"
    },

    # 🟩 CASH GREEN — Markets & Risk
    "cash": {
        "name": "Cash Green",
        "role": "markets_anchor",
        "domain": ["market structure", "volatility", "equities"],
        "voice": "confident, trader-cut",
        "cadence": "crisp, high-tempo, decisive",
        "lexicon": [
            "volatility spike",
            "order book imbalance",
            "momentum break",
            "price compression",
            "liquidation cascade"
        ],
        "avoid": [
            "technical deep dives",
            "macro gloom"
        ],
        "agreement_markers": ["absolutely", "for sure"],
        "disagreement_markers": ["but traders see", "however across markets"],
        "escalation_style": "market adrenaline escalation",
        "response_pattern": "frames trader psychology and momentum shifts"
    },

    # 🟪 PENNY LANE — Retail Investor
    "penny": {
        "name": "Penny Lane",
        "role": "retail_voice",
        "domain": ["retail sentiment", "consumer angle"],
        "voice": "friendly, curious, accessible",
        "cadence": "simple, human, relatable",
        "lexicon": [
            "everyday users",
            "real impact",
            "wallet confusion",
            "user perspective",
            "consumer cost"
        ],
        "avoid": [
            "technical jargon",
            "heavy macro talk"
        ],
        "agreement_markers": ["true", "right", "yeah"],
        "disagreement_markers": ["but from a user angle", "however for regular people"],
        "escalation_style": "empathetic escalation",
        "response_pattern": "humanizes the discussion; grounds it in real-life perspective"
    },

    # 🟥 REX VOL — Nightline Chaos Anchor
    "rex": {
        "name": "Rex Vol",
        "role": "chaos_anchor",
        "domain": ["volatility", "liquidations", "night markets"],
        "voice": "sarcastic, chaotic neutral",
        "cadence": "fast, sharp, irreverent",
        "lexicon": [
            "liquidation storm",
            "volatility bonfire",
            "chart meltdown",
            "nightline carnage",
            "leverage graveyard"
        ],
        "avoid": [
            "formal tone",
            "corporate language"
        ],
        "agreement_markers": ["lol true", "yeah that's wild"],
        "disagreement_markers": ["nah look", "but that's cope"],
        "escalation_style": "chaotic escalation",
        "response_pattern": "brings chaos energy; sharp humor; nonstop volatility tracking"
    },

    # 🟪 VEGA WATT — Vibe Director
    "vega": {
        "name": "Vega Watt",
        "role": "vibe_director",
        "domain": ["vibes", "energy", "booth commentary"],
        "voice": "musical, cool, rhythmic",
        "cadence": "smooth, hype-friendly",
        "lexicon": [
            "vibe shift",
            "energy swing",
            "tempo change",
            "groove check",
            "studio wave"
        ],
        "avoid": [
            "deep analysis",
            "cold statistics"
        ],
        "agreement_markers": ["feelin it", "true vibe"],
        "disagreement_markers": ["but the groove's off"],
        "escalation_style": "hype escalation",
        "response_pattern": "lightens mood; sets pace; booth commentary"
    }
}

# ============================================================
# PERSONA PROMPT BUILDER (news mode / latenight mode hybrid)
# ============================================================

def persona_prompt(anchor: str, brain: dict, mode: str = "news",
                   allow_multi: bool = False,
                   override_max_sentences: int = None):
    """
    Builds a persona-aware prompt wrapper for GPT text generation.

    mode="news":
        - 1 sentence MAX for all routines except gpt_analysis
        - formal, controlled, broadcaster-style
        - no slang or hyperbole
        - avoid “I”, emotional commentary, personal jokes

    mode="latenight":
        - 2–3 sentences allowed
        - humor OK, light slang OK
        - more expressive
        - conversational beats allowed

    allow_multi: overrides news 1-sentence rule (used for analysis)
    override_max_sentences: hard override (used by specific GPT routines)
    """

    style = PERSONA_STYLE.get(anchor, {})
    if not style:
        return ""  # safe fallback

    # -----------------------------------------------
    # Determine allowable sentence count
    # -----------------------------------------------
    if override_max_sentences is not None:
        max_sent = override_max_sentences
    else:
        if mode == "news":
            max_sent = 1
        else:
            max_sent = 3  # latenight expressive mode

        if allow_multi and mode == "news":
            max_sent = 3  # analysis exception

    # -----------------------------------------------
    # Rolling-brain contextual hints (soft, non-binding)
    # -----------------------------------------------
    context_lines = []
    ctx = get_context_for_anchor(anchor)
    if ctx:
        for key, val in ctx.items():
            context_lines.append(f"- {key}: {val}")

    context_str = "\n".join(context_lines) if context_lines else ""

    # -----------------------------------------------
    # Persona lexicon rules
    # -----------------------------------------------
    voice = style.get("voice", "")
    cadence = style.get("cadence", "")
    lexicon = ", ".join(style.get("lexicon", []))
    avoid = ", ".join(style.get("avoid", []))
    agree = ", ".join(style.get("agreement_markers", []))
    disagree = ", ".join(style.get("disagreement_markers", []))
    escalation = style.get("escalation_style", "")
    pattern = style.get("response_pattern", "")

    # -----------------------------------------------
    # Produce the persona control block
    # -----------------------------------------------
    p = f"""
You are **{anchor}**.

VOICE:
- {voice}

CADENCE:
- {cadence}

LEXICON PREFERENCES:
- Favor these terms: {lexicon}

AVOID:
- {avoid}

CONVERSATIONAL MOVES:
- Agreement phrases: {agree}
- Disagreement phrases: {disagree}
- Escalation style: {escalation}
- Response pattern: {pattern}

MODE RULE:
- max sentences: {max_sent}
- mode: "{mode}"

NEWS RULES (if mode == "news"):
- Keep it factual, clear, and concise.
- No slang, no hyperbole.
- No personal jokes or emotional commentary.
- MUST NOT exceed {max_sent} sentence(s).

LATENIGHT RULES (if mode == "latenight"):
- Humor OK, light slang OK.
- Conversational tone allowed.
- Can use 2–3 sentences.

ROLLING BRAIN CONTEXT:
{context_str}

Generate output following these constraints EXACTLY.
""".strip()

    return p

# ============================================================
# OPENAI WRITING ENGINE — HYBRID MODE w/ RKG + TONE GUARDRAILS
# ============================================================

import os, time, json
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


# ------------------------------------------------------------
# Core GPT Helper
# ------------------------------------------------------------
def _gpt(prompt: str) -> str:
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=180,
            temperature=0.78,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print("[OpenAIWriter] ERROR:", e)
        return None

# ============================================================
# GPT — Chip Daily Preface (Top Headlines Overview)
# ============================================================
def gpt_chip_preface(top_headlines: list, brain: dict, show_mode: str = "news"):
    """
    Chip summarizes the top ~3 headlines of the day.
    Sets tone, urgency, and narrative framing.
    2–3 sentences max. News-safe.
    """

    p = persona_prompt("chip", brain, mode=show_mode, allow_multi=True)

    # Build headline list string for GPT
    hl_text = "\n".join([f"- {h}" for h in top_headlines[:3]])

    prompt = f"""
{p}

You are opening today's live broadcast.
Summarize the major headlines below in **2–3 clear sentences**,
giving viewers the day's market pulse without hype or slang.

HEADLINES:
{hl_text}

Do NOT toss to an anchor yet.
Do NOT analyze deeply. This is a high-level morning narrative.
"""

    return _gpt(prompt)

# ============================================================
# GPT — Chip Story Intro (Framing the #1 headline)
# ============================================================
def gpt_chip_story_intro(headline: str, synthesis: str, brain: dict, show_mode: str = "news"):
    """
    Chip introduces the single main story in ~1–2 sentences.
    Tone: professional, news-safe, broadcaster style.
    No slang. No jokes. Sets the stage before tossing to anchor.
    """

    p = persona_prompt("chip", brain, mode=show_mode, allow_multi=True)

    prompt = f"""
{p}

You are Chip Blue, opening the FIRST story of today's broadcast.
Write **1–2 sentences** that professionally frame the importance,
urgency, or relevance of this headline:

"{headline}"

Use synthesis only for additional context:
"{synthesis}"

Rules:
- No slang, no jokes.
- Do NOT analyze deeply (leave that for Reef/Ledger).
- Do NOT toss to an anchor (timeline_builder handles that).
- Do NOT repeat the headline verbatim.
- Focus on framing WHY this matters today.
"""

    return _gpt(prompt)

# ============================================================
# SOLO REACTION LINE (1 sentence, news-safe)
# ============================================================
def gpt_reaction(anchor: str, headline: str, brain: dict):
    """
    Generates a single-sentence reaction fully controlled by persona_prompt().
    """
    p = persona_prompt(anchor, brain, mode="news", allow_multi=False)

    prompt = f"""
{p}

Write **exactly ONE sentence** giving a neutral, news-safe reaction
to the following headline. Do NOT add hype, slang, emotion, or claims
not supported directly by the headline.

Headline: "{headline}"
"""

    return _gpt(prompt)

def gpt_analysis(
    character: str,
    headline: str,
    synthesis: str,
    domain: str = "",
    brain: dict = None,
    show_mode: str = "news",
    **kwargs
):

    # Persona style header
    p = persona_prompt(character, brain, mode=show_mode)

    prompt = f"""
{p}

Write up to **3 sentences** analyzing the headline.

Headline: "{headline}"
Synthesis: "{synthesis}"
"""
    return _gpt(prompt)


def gpt_transition(
    anchor: str,
    headline: str,
    domain: str = "",
    brain: dict = None,
    show_mode: str = "news",
    **kwargs
):
    p = persona_prompt(anchor, brain, mode=show_mode, allow_multi=False)

    prompt = f"""
{p}

Write a clean transition line that smoothly moves from the current topic to the next.
Headline: "{headline}"
"""

    return _gpt(prompt)


def gpt_anchor_react(
    anchor: str,
    headline: str,
    domain: str = "",
    brain: dict = None,
    show_mode: str = "news",
    **kwargs
):
    p = persona_prompt(anchor, brain, mode=show_mode)

    prompt = f"""
{p}

Write a short 1-sentence emotional or reactive punchline by {anchor}.
It should be consistent with the headline:
"{headline}"
"""
    return _gpt(prompt)


# ============================================================
# DUO GPT ROUTINE — RKG-INTEGRATED HYBRID w/ CHIP FOLLOW-UP MODE
# ============================================================

def gpt_duo_line(
    speaker: str,
    counter: str,
    headline: str,
    synthesis: str,
    domain: str,
    duo_mode: str,
    last_counter_line: str = "",
    show_mode: str = "news",
    brain: dict = None,
    **kwargs
):
    p_speaker = persona_prompt(speaker, brain, mode=show_mode)
    p_counter = persona_prompt(counter, brain, mode=show_mode)

    prompt = f"""
{synthesis}

You are generating a DUO line for a crypto news broadcast.

Speaker: {speaker}
Counterpart: {counter}
Duo Mode: {duo_mode}
Headline: "{headline}"

{speaker}'s Persona:
{p_speaker}

{counter}'s Persona:
{p_counter}

Last line from the counterpart:
"{last_counter_line}"

Instructions:
- Keep it brief (1–2 sentences).
- Stay in the persona style of {speaker}.
- React directly to the counterpart when applicable.
- Do NOT repeat nouns or phrases that were already used.
- Keep professional tone in news mode.
- Get looser, more conversational in latenight mode.
"""
    return _gpt(prompt)

# ============================================================
# CHIP FOLLOW-UP REACTION (Patch 8)
# ============================================================
def gpt_chip_followup(
    primary: str,
    duo: str,
    headline: str,
    synthesis: str = "",
    last_line: str = "",
    show_mode: str = "news",
    pd_flags: dict = None,
    brain: dict = None,
    chip_domain: str = "",
    **kwargs
):
    if not chip_domain:
        chip_domain = "general"
    if pd_flags is None:
        pd_flags = {}
    if brain is None:
        brain = {}

    """
    Chip reacts to the duo with a clarifying question, insight, or nudge.
    Behavior changes based on:
        • PD flags (tragedy, volatility, sentiment, etc)
        • show_mode: "news" vs "latenight"
        • memory via brain snapshot
        • who the duo anchors were
        • last_line (contextual)
    """
    try:
        prompt = f"""
Chip is the host of TOKNNews. Generate a SINGLE sentence follow-up.

CONTEXT:
- Headline: {headline}
- Synthesis: {synthesis}
- Last duo line: "{last_line}"
- Primary anchor: {primary}
- Secondary anchor: {duo}
- Show mode: {show_mode}
- Chip domain: {chip_domain}

Brain snapshot (summaries only):
{brain.get('summary','(empty)')}

PD Flags:
{pd_flags}

RULES:
- In NEWS MODE: be sharp, factual, clarifying, direct.
- In LATENIGHT MODE: be witty, playful, but NEVER disrespect tragedy.
- If tragedy_block=True → be serious, stabilizing, empathetic.
- If volatility_risk > 0.6 → ask about market risk or protection.
- If social_heat > 0.5 → ask about sentiment, retail, or viral behavior.
- DO NOT summarize the headline; add something NEW.
- DO NOT say “absolutely,” “true,” “fair point.”
- Use 1 sentence only.
- Use host authority, NOT anchor language.

Examples:
- “Before we move on—what’s the signal retail should be watching right now?”
- “Given that shift, what’s the smartest move for builders or whales?”
- “Zoom out for me—what’s the structural force here?”

Return ONLY the sentence.
"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=80,
            temperature=0.8
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        print("[OpenAIWriter] ERROR (chip_followup):", e)
        return None

# ============================================================
# CHIP SEGMENT TOSS ENGINE (Patch 8)
# ============================================================
def gpt_chip_toss(
    next_anchor: str,
    headline: str,
    brain: dict,
    show_mode: str,
    pd_flags: dict
):
    """
    Chip tosses control to the next anchor.
    Behavior changes by show mode and PD flags.
    """
    try:
        prompt = f"""
Chip is the host. Generate a toss line directing the next anchor.

Next anchor: {next_anchor}
Headline: {headline}
Show mode: {show_mode}

Brain snapshot (summaries only):
{brain.get('summary','(empty)')}

PD Flags:
{pd_flags}

RULES:
- NEWS MODE: crisp, professional, forward-driving.
- LATENIGHT MODE: fun, quick-witted, playful — but avoid comedy if tragedy_block=True.
- 1 sentence only.
- No filler like “Alright” or “Okay.”
- Use anchor’s name naturally.
- Keep momentum into next segment.

Examples:
- “Rex, take us deeper into the volatility drivers here.”
- “Ivy, what’s the community temperature after this move?”
- “Bitsy, give us the vibe check from across the timeline.”
- “Lawson, walk us through the fundamentals under pressure.”

Return ONLY the sentence.
"""

        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=60,
            temperature=0.8
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        print("[OpenAIWriter] ERROR (chip_toss):", e)
        return f"{next_anchor}, take it from here."
