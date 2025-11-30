# voice_map.py
# TOKEN NEWS — ElevenLabs Voice ID Mapping
# Maps all personas to their assigned ElevenLabs voices.
# --------------------------------------------------------------------

VOICE_MAP = {

    # =======================
    # FLAGSHIP ANCHOR
    # =======================
    "chip": "teAyVVX8spybXkITa1A0",          # Chip_Blue

    # =======================
    # MARKET PSYCHOLOGY
    # =======================
    "cash": "b2zP5WtU6zW1RDLwR1VL",          # Cash_Green

    # =======================
    # AI / COMPUTE ANALYSIS
    # =======================
    "neura": "U21zT7YnOSlmiJ6Uzs70",         # Neura_Grey

    # =======================
    # ON-CHAIN ANALYTICS
    # =======================
    "ledger": "NZN55afVwq1WHQJOwDCz",        # Ledger_Stone

    # =======================
    # LEGAL / REGULATORY
    # =======================
    "lawson": "Wz0W8ilvy9oYu7DeKWfB",        # Lawson_Black

    # =======================
    # DEFI SPECIALIST
    # =======================
    "reef": "7pLXpsTZ3rOalpNWmYqI",          # Reef_Gold

    # =======================
    # VENTURE / FUNDING
    # =======================
    "cap": "eeFsfJ0uulJx6xKTmsRE",           # Cap_Silver

    # =======================
    # MACRO STRATEGIST
    # =======================
    "bond": "ckPPrwZqzA7Vp7ceNunQ",          # Bond_Crimson

    # =======================
    # BEHAVIORAL ECONOMICS
    # =======================
    "ivy": "Iw2tTyxZnwTODhsmOq00",           # Ivy_Quinn

    # =======================
    # META CHAOS / INTERRUPT
    # =======================
    "bitsy": "VOkhRocQyiAQg2RF9A5e",         # Bitsy_Gold

    # =======================
    # RETAIL / LIFESTYLE
    # =======================
    "penny": "7WqwVs6Wqe0yEev6QDxV",         # Penny_Lane

    # =======================
    # NIGHTLINE VOLATILITY
    # =======================
    "rex": "5Rbobt83lpNwhTQEhH2F",           # Rex_Vol

    # =======================
    # BOOTH VOICEOVER
    # =======================
    "vega": "Ax1HxHll9ku8pGyIt6kK",           # Vega_Watt
}

# --------------------------------------------------------------------
# SAFE FALLBACK
# --------------------------------------------------------------------
DEFAULT_VOICE_ID = VOICE_MAP["chip"]


def get_voice_id(persona: str) -> str:
    """
    Return the ElevenLabs voice ID for a persona.
    Falls back to Chip if persona not recognized.
    """
    persona = (persona or "").lower().strip()
    return VOICE_MAP.get(persona, DEFAULT_VOICE_ID)
