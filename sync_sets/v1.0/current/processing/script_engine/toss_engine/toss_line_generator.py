# backend/script_engine/toss_engine/toss_line_generator.py

TONE_TEMPLATES = {
    "positive": [
        "Good news developing here — {anchor} has more.",
        "{anchor} is tracking some encouraging movement on this.",
        "A promising update — {anchor} has the details."
    ],
    "negative": [
        "A concerning development — {anchor} is following this closely.",
        "Not the best news — {anchor} breaks it down.",
        "{anchor} has the latest on a story raising some eyebrows."
    ],
    "neutral": [
        "Here’s what we know so far — {anchor} has more.",
        "{anchor} walks us through the latest.",
        "Let’s take a closer look — {anchor} has the breakdown."
    ]
}

DAYPART_TEMPLATES = {
    "morning": [
        "Starting off this morning, {anchor} has more.",
        "Here’s how we're kicking off the day — {anchor} breaks it down.",
        "A morning update — {anchor} has the latest."
    ],
    "afternoon": [
        "This afternoon, {anchor} has the read.",
        "{anchor} walks us through the mid-day update.",
        "A developing story this afternoon — {anchor} explains."
    ],
    "evening": [
        "Tonight, {anchor} brings us the details.",
        "A key update this evening — {anchor} breaks it down.",
        "Here's where things stand tonight — {anchor} has more."
    ],
    "late_night": [
        "Late tonight, {anchor} has more on this.",
        "As the day winds down, {anchor} walks us through it.",
        "A late-night development — {anchor} breaks it down."
    ],
    "breaking": [
        "Breaking at this hour — {anchor} has the latest.",
        "{anchor} is on this breaking story now.",
        "We’re following this breaking development — {anchor} brings us inside."
    ]
}

DOMAIN_TEMPLATES = {
    "ai": [
        "On the AI front, {anchor} has more.",
        "{anchor} is following this one on the AI side.",
        "Developments in AI today — {anchor} breaks it down."
    ],
    "venture": [
        "In the funding world, {anchor} has the details.",
        "Another big venture move — {anchor} explains.",
        "{anchor} is tracking the latest in startup capital."
    ],
    "markets": [
        "Turning to the markets, {anchor} has more.",
        "{anchor} is keeping a close eye on the market reaction.",
        "A shift in the markets — {anchor} has the read."
    ],
    "defi": [
        "In the DeFi space, {anchor} walks us through it.",
        "{anchor} has the latest from the decentralized finance world.",
        "A DeFi move worth noting — {anchor} explains."
    ],
    "regulation": [
        "In Washington, {anchor} is tracking this development.",
        "{anchor} breaks down the regulatory side.",
        "A policy angle here — {anchor} explains what it means."
    ],
    "security": [
        "A new security concern tonight — {anchor} has more.",
        "{anchor} is monitoring the security implications.",
        "On the cyber front, {anchor} breaks it down."
    ],
    "culture": [
        "In the digital culture scene, {anchor} has the story.",
        "{anchor} follows this one from the creator side.",
        "A culture moment — {anchor} has more."
    ],
}

# Stage 4 persona templates
CHIP_PERSONA_TEMPLATES = {
    "positive": [
        "Looking good. {base}",
        "Momentum looks solid. {base}",
        "Let’s keep this tight. {base}"
    ],
    "neutral": [
        "Let’s break this one down. {base}",
        "Straight to it. {base}",
        "Here’s what we know. {base}"
    ],
    "negative": [
        "Not ideal. {base}",
        "This one’s a concern. {base}",
        "Let’s keep an eye on this. {base}"
    ]
}

# Stage 5 modulation templates
CHIP_MODULATION = {
    "skeptical": [
        "Let’s keep expectations in check. {base}",
        "I’m not entirely convinced. {base}",
        "We’ve seen this movie before. {base}"
    ],
    "serious": [
        "Let’s take this one seriously. {base}",
        "This is important. {base}",
        "We need to watch this closely. {base}"
    ],
    "hyped": [
        "This could be big. {base}",
        "Feels like something’s brewing here. {base}",
        "Eyes on this one. {base}"
    ],
    "cautious": [
        "Let’s tread carefully. {base}",
        "A lot can go wrong here—{base}",
        "We’ll need to see how this develops. {base}"
    ],
    "sarcastic": [
        "Oh great, here we go again. {base}",
        "Totally didn’t see *that* coming. {base}",
        "Classic move. {base}"
    ]
}

BREAKING_TEMPLATES = {
    1: [
        "Worth keeping an eye on this.",
        "This could develop quickly.",
        "A notable shift here."
    ],
    2: [
        "This one matters.",
        "A significant development is unfolding.",
        "We need to pay close attention here."
    ],
    3: [
        "Breaking news just in.",
        "We’re following this right now.",
        "This is developing as we speak."
    ]
}

# Late-night sarcasm pool (Stage 5-D)
LATE_NIGHT_SARCASM = [
    "Alright, it’s officially too late for this.",
    "This is what happens when you stay up watching charts.",
    "At this hour? Really?",
    "Should’ve gone to bed, but here we are.",
    "If you’re still awake watching ToknNews… respect."
   ]

ANCHOR_TEMPLATES = {
    "Neura Grey": [
        "Neura, walk us through it.",
        "Neura, break this down.",
        "Your read on this, Neura?"
    ],
    "Cash Green": [
        "Cash, what’s your read?",
        "Cash, talk us through the move.",
        "Cash, set the stage for us."
    ],
    "Reef Gold": [
        "Reef, unpack this.",
        "Reef, what's happening here?",
        "Reef, give us the pulse."
    ],
    "Lawson Black": [
        "Lawson, what are we looking at?",
        "Lawson, help us understand the angle.",
        "Lawson, walk us through the policy side."
    ],
    "Ivy Quinn": [
        "Ivy, what stands out?",
        "Ivy, walk us through the highlight.",
        "Ivy, bring us inside the trend."
    ],
    "Bitsy Gold": [
        "Bitsy, flag anything weird.",
        "Bitsy, what are you seeing here?",
        "Bitsy, drop us a quick pulse check."
    ],
    "Vega Watt": [
        "Vega, set the vibe.",
        "Vega, what's the energy on this?",
        "Vega, give us a read before we dive in."
    ]
}

def choose_chip_modulation(enriched, daypart):
    sentiment = enriched.get("sentiment", "neutral")
    importance = enriched.get("importance", 5)
    domain = enriched.get("domain", "general")

    # Breaking-news override (we handle more in stage 5-E)
    if importance >= 9:
        return "serious"

    # Negative news → skeptical or serious
    if sentiment == "negative":
        if domain in ["regulation", "security"]:
            return "serious"
        return "skeptical"

    # Positive news → hyped for major stories
    if sentiment == "positive":
        if importance >= 7:
            return "hyped"

    # Regulatory or SEC → cautious
    if domain == "regulation":
        return "cautious"

    # Late night mode → light sarcasm
    if daypart == "late_night":
        return "sarcastic"

    # Default → none (use base toss)
    return None

def choose_breaking_overlay(escalation_level):
    """Returns breaking overlay text or None."""
    if escalation_level is None or escalation_level <= 0:
        return None

    pool = BREAKING_TEMPLATES.get(escalation_level)
    if not pool:
        return None

    import random
    return random.choice(pool)

def build_chip_toss(enriched):
    """
    Tone-aware toss generator for Chip Blue.
    NEVER includes headline text.
    Uses sentiment, domain, time-of-day, and importance.
    """

    anchor = enriched.get("primary_character", "the team")
    sentiment = enriched.get("sentiment", "neutral").lower()
    domain = enriched.get("domain", "general").lower()
    importance = enriched.get("importance", 5)

    # --- Tone libraries (Chip style) ---
    sentiment_tones = {
        "positive": [
            "Promising move here —",
            "Tailwinds showing —",
            "Looking solid —"
        ],
        "negative": [
            "Let’s stay sharp on this one —",
            "Not ideal here —",
            "This one’s concerning —"
        ],
        "neutral": [
            "Alright —",
            "Let’s walk through this —",
            "Steady update here —"
        ]
    }

    domain_tones = {
        "markets": [
            "Market’s shifting —",
            "Volatility picking up —",
            "Let’s check the price action —"
        ],
        "defi": [
            "DeFi’s moving again —",
            "On-chain’s heating up —",
            "Protocol-wise —"
        ],
        "ai": [
            "AI’s driving this one —",
            "Tech moving fast again —",
            "Model-side —"
        ],
        "regulation": [
            "Policy angle on this —",
            "Washington’s moving —",
            "Legal side of things —"
        ],
        "security": [
            "Security note here —",
            "We should unpack this —",
            "Cyber angle —"
        ]
    }

    # --- fallback libraries ---
    fallback_tones = [
        "Let’s take this one —",
        "Alright —",
        "Here we go —"
    ]

    # --- late-night flavor ---
    from script_engine.time_logic import get_broadcast_time_info
    ti = get_broadcast_time_info()
    if ti["hour"] >= 22 or ti["hour"] < 2:
        late_night = [
            "At this hour? Okay —",
            "Still with us? —",
            "Late-night check-in —"
        ]
    else:
        late_night = None

    # --- choose tone ---
    import random
    tone_pool = []

    # sentiment first
    tone_pool.extend(sentiment_tones.get(sentiment, []))

    # domain second
    tone_pool.extend(domain_tones.get(domain, []))

    # fallback
    tone_pool.extend(fallback_tones)

    # add late-night spice if applicable
    if late_night:
        tone_pool.extend(late_night)

    tone = random.choice(tone_pool)

    # --- Anchor cue (never headline) ---
    anchor_cues = [
        f"{anchor}, what’s your read?",
        f"{anchor}, walk us through it.",
        f"{anchor}, help us understand the angle.",
        f"{anchor}, take us inside the move.",
        f"{anchor}, break this down for us."
    ]
    anchor_line = random.choice(anchor_cues)

    # --- Final toss (no headline allowed) ---
    return f"{tone} {anchor_line}"
