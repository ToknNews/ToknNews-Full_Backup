#!/usr/bin/env python3
"""
grok_writer.py  
TOKEN NEWS — Character Conversation Engine (OpenAI)

Provides high-level generation of multi-line dialogues between anchor characters for Token News.
Replaces legacy line-by-line Grok (xAI) generation with full-block conversation using OpenAI GPT models.
"""

import os
import time
import json
from openai import OpenAI

# Load OpenAI API key from vault
from backend.runtime.vault_loader import load_secrets
OPENAI_API_KEY = load_secrets().get("openai_api_key", "")
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# ============================================================
# Conversation Block Generator
# ============================================================
def write_block_conversation(primary: str,
                             headline: str,
                             synthesis: str = "",
                             scene_state: dict = None,
                             episode_id: str = "",
                             secondary: str = None) -> str:
    """
    Generate a full multi-line dialogue between Chip and other anchor(s) about the given story.
    - primary: the main anchor for the story (other than Chip).
    - secondary: an optional second anchor for a trio conversation.
    Returns a formatted multi-line string with speaker labels (e.g., "Chip: ...").
    """
    primary = primary.lower()
    secondary = secondary.lower() if secondary else None
    # Determine which anchor characters will participate (excluding Chip if listed)
    other_names = [primary] if primary != "chip" else []
    if secondary and secondary != "" and secondary != primary:
        other_names.append(secondary)
    other_names = [name for name in other_names if name and name != "chip"]
    # If there's no other anchor to converse with (e.g., primary is Chip), fall back to a simple line
    if not other_names:
        return f"{primary.capitalize()}: {synthesis or '...'}"
    # Build persona profiles for Chip and the other anchor(s)
    from script_engine.character_brain.persona_prompt_config import PERSONA_PROMPT_CONFIG
    def get_persona_profile(name: str) -> str:
        profile = PERSONA_PROMPT_CONFIG.get(name.lower(), {}).get("gpt_prompt_seed", "")
        if profile:
            # Convert persona description to third person (for prompt context)
            desc = profile
            if desc.startswith(f"You are {name.capitalize()},"):
                desc = desc.replace(f"You are {name.capitalize()},", f"{name.capitalize()} is", 1)
            if ". You " in desc:
                desc = desc.replace(". You ", f". {name.capitalize()} ", 1)
            # Adjust common verbs to third-person form
            for verb in ["speak", "talk", "think", "analyze", "interpret", "break", "translate", "interrupt"]:
                desc = desc.replace(f"{name.capitalize()} {verb} ", f"{name.capitalize()} {verb}s ")
            # Fix multi-verb phrases for grammatical correctness
            if "talks fast, think faster," in desc:
                desc = desc.replace("talks fast, think faster,", "talks fast, thinks faster,")
            if "wall, interrupt with" in desc:
                desc = desc.replace("wall, interrupt with", "wall, interrupts with")
            return desc.strip()
        else:
            # Fallback generic identity if no profile found
            return f"{name.capitalize()} is an anchor on Token News with a unique style."
    chip_profile = get_persona_profile("chip")
    profiles = {name: get_persona_profile(name) for name in other_names}
    # Build the conversation prompt with roles and context
    other_display = " and ".join(n.capitalize() for n in other_names)
    characters_section = "Characters:\n"
    characters_section += f"- {chip_profile}\n"
    for name in other_names:
        characters_section += f"- {profiles[name]}\n"
    prompt = (
        "The following is a conversation on Token News about a story.\n"
        f"Headline: {headline}\n"
        f"Summary: {synthesis}\n\n"
        f"{characters_section}\n"
        "Instructions:\n"
        f"- Chip (the host) should start by asking a question or prompting {other_names[0].capitalize()}.\n"
        "- Chip remains calm, guiding the discussion.\n"
        f"- {other_display} {'are' if len(other_names)>1 else 'is'} more impulsive or colorful in commentary.\n"
        + ("- The other anchors may banter with each other while Chip moderates.\n" if secondary and secondary.lower() in other_names else "")
        + "- Keep the dialogue realistic, coherent, and highly entertaining.\n"
        "- Do not simply repeat the headline; discuss implications or context.\n"
        "- No filler greetings or sign-offs.\n"
        "- Aim for about 4 to 6 lines of dialogue in total.\n"
        "- Use each speaker's name followed by a colon for their dialogue.\n"
        "- Only output the dialogue lines (no descriptions or stage directions).\n"
    )
    # Call OpenAI to generate the conversation block
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=180,
            temperature=0.8
        )
        conv_text = response.choices[0].message.content.strip()
    except Exception as e:
        print("[GrokWriter] ERROR generating conversation:", e)
        # Fallback to a simple exchange if the API call fails
        if secondary and secondary.lower() in other_names:
            return (f"Chip: {headline}?\\n"
                    f"{other_names[0].capitalize()}: This is big news, Chip.\\n"
                    f"{other_names[1].capitalize()}: Absolutely, quite a story.")
        else:
            return (f"Chip: {headline}?\\n"
                    f"{other_names[0].capitalize()}: Certainly, it's an important update.")
    # Clean up any extraneous formatting (remove wrapping quotes or code blocks if present)
    conv_text = conv_text.strip().strip('"').strip("```").strip()
    return conv_text
