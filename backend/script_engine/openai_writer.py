#!/usr/bin/env python3
"""
grok_writer.py
TOKEN NEWS — GPT Writing Engine (Clean Rebuild, 2025)

This module provides:
 - intro
 - transitions (including next-anchor handoff)
 - analysis
 - reactions
 - duo exchanges
 - breaking news
 - syntheses

Fully compatible with timeline_builder (2025 rebuild).
"""

import os
import time
import json
from openai import OpenAI

# Runtime components
from runtime.scene_state import build_scene_state
from runtime.persona_style_overlay import build_style_overlay
from runtime.persona_mood_model import update_persona_mood
from runtime.conversation_memory import build_memory_context, store_short_term

# Persona + voice config
from script_engine.character_brain.persona_prompt_config import PERSONA_PROMPT_CONFIG
from script_engine.persona.voice_map import VOICE_MAP

# Vault secrets
from backend.runtime.vault_loader import load_secrets
OPENAI_API_KEY = load_secrets()["openai_api_key"]
client = OpenAI(api_key=OPENAI_API_KEY)



# ============================================================
# MODEL SELECTION
# ============================================================

def choose_model(task_type: str) -> str:
    """Model Strategy v2."""
    if task_type in ["analysis", "duo", "breaking", "synthesis"]:
        return "gpt-4o"
    if task_type in ["reaction", "toss"]:
        return "gpt-4o-mini"
    if task_type in ["transition", "intro"]:
        return "gpt-4.1-mini"
    return "gpt-4o-mini"



# ============================================================
# UNIFIED GPT CALL
# ============================================================

def gpt_call(model: str, prompt: str, max_tokens=160, temperature=0.7):
    """Core OpenAI handler with fallback."""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature
        )
        return resp.choices[0].message.content.strip()

    except Exception as e:
        print("[OpenAIWriter] ERROR:", e)
        print("[OpenAIWriter] Retrying with gpt-4.1-mini…")

        try:
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature
            )
            return resp.choices[0].message.content.strip()
        except Exception as e2:
            print("[OpenAIWriter] CRITICAL FAILURE:", e2)
            return None



# ============================================================
# PERSONA SEED & EXAMPLES
# ============================================================

def build_persona_seed(persona: str) -> str:
    cfg = PERSONA_PROMPT_CONFIG.get(persona.lower(), {})
    return cfg.get("gpt_prompt_seed", f"You are {persona}, an anchor on Token News.")


def build_persona_examples(persona: str) -> str:
    cfg = PERSONA_PROMPT_CONFIG.get(persona.lower(), {})
    examples = cfg.get("example_lines", [])

    if not examples:
        return ""

    block = "Examples of your tone:\n"
    for line in examples[:3]:
        block += f"- {line}\n"
    return block



# ============================================================
# SYSTEM PROMPT BUILDER
# ============================================================

def build_system_context(persona: str, scene_state: dict, memory_context: dict, mood: float):
    persona = persona.lower()

    persona_seed = build_persona_seed(persona)
    example_block = build_persona_examples(persona)

    style_overlay = build_style_overlay(
        persona=persona,
        daypart=scene_state["daypart"],
        show_mode=scene_state["show_mode"],
        pd_flags=scene_state["pd_flags"],
        mood=mood,
        memory_context=memory_context
    )

    state_json = json.dumps(scene_state, indent=2)
    memory_json = json.dumps(memory_context, indent=2)

    return f"""
You are {persona.capitalize()}, an anchor on Token News.

PERSONA IDENTITY:
{persona_seed}

STYLE OVERLAY:
{style_overlay}

TONE ANCHORS:
{example_block}

SCENE STATE:
{state_json}

CONVERSATION MEMORY:
{memory_json}

GENERAL RULES:
- Stay strictly in persona.
- No hype, no filler.
- No greetings.
- Do NOT repeat or summarize the headline.
- No speaker labels.
- Broadcast pacing only.
"""



# ============================================================
# WRITE-LINE (CORE ROUTER)
# ============================================================

def write_line(task_type: str,
               persona: str,
               headline: str,
               synthesis: str,
               scene_state: dict,
               episode_id: str,
               block_index: int,
               next_anchor: str):
    """
    Core router for timeline_builder.
    """

    persona = persona.lower()
    memory_context = build_memory_context(persona, episode_id)

    mood = update_persona_mood(
        persona=persona,
        pd_flags=scene_state["pd_flags"],
        daypart=scene_state["daypart"],
        memory_context=memory_context
    )

    system_prompt = build_system_context(
        persona=persona,
        scene_state=scene_state,
        memory_context=memory_context,
        mood=mood
    )

    model = choose_model(task_type)

    # Task routing
    if task_type == "intro":
        return write_intro(system_prompt, model)

    if task_type == "analysis":
        return write_analysis(system_prompt, model, headline, synthesis)

    if task_type == "reaction":
        return write_reaction(system_prompt, model, headline)

    if task_type == "transition":
        return write_transition(system_prompt, model, headline, next_anchor)

    if task_type == "toss":
        return write_chip_toss(system_prompt, model, persona, headline)

    if task_type == "duo":
        return write_duo(system_prompt, model, persona, headline, scene_state)

    if task_type == "breaking":
        return write_breaking(system_prompt, model, headline, synthesis)

    if task_type == "synthesis":
        return write_synthesis(system_prompt, model, headline, synthesis)

    print("[OpenAIWriter] Unknown task:", task_type)
    return None



# ============================================================
# SAFE WRAPPER
# ============================================================

def write_line_safe(task_type: str,
    max_words: int = None,
    max_words: int = None,
                    persona: str,
                    headline: str = "",
                    synthesis: str = "",
                    scene_state: dict = None,
                    episode_id: str = "",
                    block_index: int = 0,
                    next_anchor: str = ""):

    raw = write_line(
        task_type=task_type,
        persona=persona,
        headline=headline,
        synthesis=synthesis,
        scene_state=scene_state,
        episode_id=episode_id,
        block_index=block_index,
        next_anchor=next_anchor
    )

    cleaned = clean_response(raw)
    if cleaned:
        store_short_term(episode_id, block_index, persona, cleaned)
        return cleaned

    print(f"[OpenAIWriter] Fallback triggered for persona={persona}, task={task_type}")
    return f"{persona.capitalize()} offers a brief commentary."



# ============================================================
# GENERATOR FUNCTIONS
# ============================================================

def write_intro(system_prompt, model):
    prompt = f"""
{system_prompt}

TASK:
Write a single broadcast-ready introduction line.

Rules:
- Exactly 1 sentence.
- No greetings (Chip intro handled in timeline_builder).
- No headline references.
"""
    return gpt_call(model, prompt, max_tokens=45, temperature=0.55)



def write_analysis(system_prompt, model, headline, synthesis):
    prompt = f"""
{system_prompt}

TASK:
Provide concise anchor analysis.

HEADLINE: {headline}
SYNTHESIS: {synthesis}

Rules:
- 2–4 sentences.
- Add insight, NOT summary.
- Maintain persona worldview.
"""
    return gpt_call(model, prompt, max_tokens=200, temperature=0.7)



def write_reaction(system_prompt, model, headline):
    prompt = f"""
{system_prompt}

TASK:
Provide a short reaction to the headline.

Rules:
- 1 sentence.
- Do NOT repeat headline nouns.
"""
    return gpt_call(model, prompt, max_tokens=60, temperature=0.6)



def write_duo(system_prompt, model, persona, headline, scene_state):
    last = scene_state.get("previous_line", {})
    prev_speaker = last.get("speaker", "the other anchor")
    prev_line = last.get("text", "")

    prompt = f"""
{system_prompt}

TASK:
Respond directly to the previous anchor in a duo exchange.

PREVIOUS SPEAKER: {prev_speaker}
THEIR LINE: "{prev_line}"

Rules:
- 1–2 sentences.
- React to THEM, not the headline.
- Add tension when story heat is high.
"""
    return gpt_call(model, prompt, max_tokens=100, temperature=0.75)



def write_chip_toss(system_prompt, model, persona, headline):
    prompt = f"""
{system_prompt}

TASK:
Chip hands off to the next anchor.

Rules:
- 1 sentence.
- Professional, neutral.
- Address the anchor by name.
"""
    return gpt_call(model, prompt, max_tokens=55, temperature=0.55)



def write_transition(system_prompt, model, headline, next_anchor):
    # Preferred: direct anchor handoff
    if next_anchor:
        prompt = f"""
{system_prompt}

TASK:
Write a ONE-sentence transition from Chip TO {next_anchor}.

Rules:
- EXACTLY 1 sentence.
- No headline words.
- No summary.
- No analysis.
- Clean handoff patterns like:
  “{next_anchor.capitalize()}, what’s your take on this?”
  “{next_anchor.capitalize()}, walk us through this one.”
  “{next_anchor.capitalize()}, give us the perspective here.”
"""
        return gpt_call(model, prompt, max_tokens=40, temperature=0.50)

    # fallback neutral transition
    prompt = f"""
{system_prompt}

TASK:
Write a ONE-sentence transition into the next story.

Rules:
- 1 sentence.
- No summary.
- No analysis.
"""
    return gpt_call(model, prompt, max_tokens=35, temperature=0.45)



def write_breaking(system_prompt, model, headline, synthesis):
    prompt = f"""
{system_prompt}

TASK:
Deliver a breaking news update.

HEADLINE: {headline}
CONTEXT: {synthesis}

Rules:
- 1–2 short sentences.
- Serious tone.
"""
    return gpt_call(model, prompt, max_tokens=100, temperature=0.4)



def write_synthesis(system_prompt, model, headline, synthesis_text):
    prompt = f"""
{system_prompt}

TASK:
Synthesize this into a concise insight.

HEADLINE: {headline}
SYNTHESIS: {synthesis_text}

Rules:
- Exactly 2 sentences.
- Add value, no repetition.
- Avoid reused nouns.
"""
    return gpt_call(model, prompt, max_tokens=120, temperature=0.6)



# ============================================================
# RESPONSE CLEANUP
# ============================================================

def clean_response(text):
    if not text:
        return None

    t = text.strip()

    if t.startswith('"') and t.endswith('"'):
        t = t[1:-1].strip()

    lowers = t.lower()
    for p in ["chip:", "reef:", "bond:", "cash:", "ledger:", "lawson:"]:
        if lowers.startswith(p):
            return t.split(":",1)[1].strip()

    return t



# ============================================================
# EXPORTS
# ============================================================

__all__ = [
    "write_line",
    "write_line_safe",
    "choose_model"
]
