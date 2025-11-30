#!/usr/bin/env python3
"""
GPT Persona Writer v1
---------------------

This module turns story context + persona DNA into a polished,
fully-realized spoken line ready for ElevenLabs + Unreal.

It is the SINGLE entrypoint for all character speech.
"""

import json
import os
from openai import OpenAI

# Load Persona DNA (character_brain.json)
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BRAIN_PATH = os.path.join(BASE_DIR, "character_brain", "character_brain.json")

def load_brain():
    try:
        with open(BRAIN_PATH, "r") as f:
            return json.load(f)
    except:
        return {}

# Create GPT client
client = OpenAI()

def generate_gpt_persona_line(character, enriched):
    """
    Returns a natural, persona-aware spoken line using GPT.
    
    Inputs:
        - character: "Chip Blue", "Neura Grey", etc.
        - enriched: full enriched story dict from Script Engine v3

    Output:
        - One polished spoken line, ready for ElevenLabs.
    """

    brain = load_brain()
    profile = brain.get(character, {})

    if not profile:
        return f"{character} says: {enriched.get('summary','')}"

    # Build the master persona prompt
    prompt = f"""
You are writing a single spoken line for **{character}** on ToknNews.

### Persona Profile:
{json.dumps(profile, indent=2)}

### Story Context:
Headline: {enriched.get("headline")}
Summary: {enriched.get("summary")}
Sentiment: {enriched.get("sentiment")}
Importance: {enriched.get("importance")}
Domain: {enriched.get("domain")}
Escalation Level: {enriched.get("escalation_level",0)}

### Additional Context
Risk Meter: {enriched.get("risk_line","")}
Comparative Angle: {enriched.get("comparative_line","")}
Theme Highlight: {enriched.get("theme_line","")}
Recent Stories: {enriched.get("recent_stories",[])}

### Instructions:
- Produce **ONE spoken sentence** (not multiple).
- Keep it human, conversational, natural.
- Maintain the character's persona and speaking style.
- Include subtle tonal cues (emotion, stress, urgency).
- Avoid narration; this must sound like real speech.
- Never repeat the headline verbatim.
- Do NOT include quotes around the output.
- This line must be immediately usable for ElevenLabs and Unreal.

### Output:
A single spoken line for {character}.
"""

    # GPT call
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role":"system","content":"You generate natural TV-anchor dialogue."},
            {"role":"user","content":prompt}
        ],
        max_tokens=80,
        temperature=0.9
    )

    line = response.choices[0].message.content.strip()

    # Safety cleanup
    line = line.replace('"','').replace("'", "'")

    return line
