#!/usr/bin/env python3
"""
TOKN Control Studio — Full Persona-Aware LLM Engine (Fixed Version)
"""

import json
import time
from pathlib import Path
from flask import Blueprint, request, jsonify
from openai import OpenAI

from backend.internal.security.totp import load_state
from backend.script_engine.context_router import route_persona_for_headline
from backend.script_engine.character_brain.persona_loader import load_persona

llm_bp = Blueprint("studio_llm", __name__, url_prefix="/api/studio/llm")
client = OpenAI()

# ----------------------------------------------------------
# Paths
# ----------------------------------------------------------
ROLLING_STORIES = Path("/opt/toknnews/data/rolling_stories.json")
CLUSTERS_PATH   = Path("/opt/toknnews/data/analytics/clusters.json")

QUEUE_PATH      = Path("/opt/toknnews/data/pipeline/queued_segments.json")
STORYBANK_PATH  = Path("/opt/toknnews/data/storybank/storybank.json")
STORYBANK_PATH.parent.mkdir(parents=True, exist_ok=True)


# ----------------------------------------------------------
# Guard
# ----------------------------------------------------------
def guard():
    if load_state() != "SETUP_COMPLETE":
        return False, jsonify({"ok": False, "error": {"message": "Setup incomplete."}}), 403
    return True, None, None


# ----------------------------------------------------------
# Load Data
# ----------------------------------------------------------
def load_rolling():
    try:
        if ROLLING_STORIES.exists():
            return json.loads(ROLLING_STORIES.read_text())
    except:
        pass
    return []

def load_clusters():
    try:
        if CLUSTERS_PATH.exists():
            wrapper = json.loads(CLUSTERS_PATH.read_text())
            if wrapper:
                return wrapper[0].get("clusters", [])
    except:
        pass
    return []


# ----------------------------------------------------------
# Model Auto-Select
# ----------------------------------------------------------
MODEL_ORDER = [
    "gpt-4o-2024-08-06",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-o",
    "gpt-4.1",
    "gpt-4.1-mini"
]

def select_model(requested):
    if requested == "auto":
        try_list = MODEL_ORDER
    else:
        try_list = [requested] + [m for m in MODEL_ORDER if m != requested]

    for model in try_list:
        try:
            client.models.retrieve(model)
            return model
        except Exception:
            continue

    return "gpt-4o-mini"


# ----------------------------------------------------------
# Persona Routing + Warnings
# ----------------------------------------------------------
def recommended_persona_for_signals(signals):
    headline = signals[0] if signals else "general crypto"
    persona = route_persona_for_headline(headline)
    return persona.lower().strip()

def maybe_warn(selected, recommended):
    s = selected.lower().strip()
    if s == recommended:
        return None
    return f"Recommended persona is '{recommended}', but '{selected}' was selected."


# ----------------------------------------------------------
# LateNight Overrides (Hybrid LN-C)
# ----------------------------------------------------------
def apply_latenight_overrides(persona, persona_data, ln_mode):
    if not ln_mode:
        return persona_data

    enriched = persona_data.copy()

    # Persona-specific latenight block
    if "latenight" in persona_data:
        ln = persona_data["latenight"]
        extra = ln.get("phrasing_add", [])
        dna_extra = [f"(LateNight) {p}" for p in extra]
        enriched["persona"] = persona_data.get("persona", []) + dna_extra
        return enriched

    # General LN fallback
    fallback = [
        "(LateNight) tone: slightly more expressive and humorous.",
        "(LateNight) commentary permitted, remain persona-accurate.",
        "(LateNight) energy elevated."
    ]
    enriched["persona"] = persona_data.get("persona", []) + fallback
    return enriched


# ----------------------------------------------------------
# Extract Top Signals (D2)
# ----------------------------------------------------------
def top_signals(query, stories, clusters):
    q = query.lower()

    # Cluster match first
    cluster_hits = []
    for cl in clusters:
        if any(q in s.lower() for s in cl.get("stories", [])):
            cluster_hits.append(cl)

    if cluster_hits:
        cluster_hits.sort(key=lambda c: len(c.get("stories", [])), reverse=True)
        sel = cluster_hits[0]
        return sel.get("name"), sel.get("summary"), sel.get("stories", [])[:15]

    # Direct story match
    direct_hits = []
    for s in stories:
        block = json.dumps(s).lower()
        if q in block:
            title = s.get("title") or s.get("headline") or None
            if title:
                direct_hits.append(title)

    return "General Narrative", "General activity detected.", direct_hits[:15]


# ----------------------------------------------------------
# Build Prompt
# ----------------------------------------------------------
def build_prompt(persona, persona_data, signals):
    dna = "\n".join([f"* {line}" for line in persona_data.get("persona", [])])
    analysis_style = persona_data.get("analysis_style", {}).get("core", "")
    lex_pref = persona_data.get("lexicon", {}).get("preferred", [])
    lex_avoid = persona_data.get("lexicon", {}).get("avoid", [])
    signal_block = "\n".join([f"- {s}" for s in signals])

    return (
        "You are writing a ToknNews narration.\n\n"
        f"Persona: {persona}\n\n"
        f"Persona DNA:\n{dna}\n\n"
        f"Analysis Style:\n{analysis_style}\n\n"
        f"Preferred Vocabulary: {', '.join(lex_pref)}\n"
        f"Avoid: {', '.join(lex_avoid)}\n\n"
        f"Signals to integrate:\n{signal_block}\n\n"
        "Rules:\n"
        "- 5–7 sentences.\n"
        "- Stay in persona.\n"
        "- Do NOT hype or speculate.\n"
        "- Do NOT repeat the query.\n"
    )


# ----------------------------------------------------------
# (1) LLM From Concept
# ----------------------------------------------------------
@llm_bp.post("/generate_segment")
def generate_segment():
    ok, resp, code = guard()
    if not ok:
        return resp, code

    data      = request.json or {}
    concept   = data.get("concept", "").strip()
    persona   = data.get("persona", "chip").lower()
    model_in  = data.get("model", "auto")
    ln_mode   = data.get("latenight", False)

    persona_data = apply_latenight_overrides(persona, load_persona(persona), ln_mode)
    model = select_model(model_in)

    # Build prompt
    dna = "\n".join([f"* {l}" for l in persona_data.get("persona", [])])
    prompt = (
        f"Write a ToknNews narration in persona '{persona}'.\n\n"
        f"Concept: \"{concept}\"\n\n"
        f"Persona DNA:\n{dna}\n\n"
        "Rules:\n- 5–7 sentences.\n- Structured.\n- Persona accurate.\n"
    )

    try:
        out = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300
        )
        script = out.choices[0].message.content  # FIXED

        recommended = recommended_persona_for_signals([concept])
        warn = maybe_warn(persona, recommended)

        return jsonify({
            "ok": True,
            "script": script,
            "persona": persona,
            "recommended_persona": recommended,
            "model_used": model,
            "warning": warn
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ----------------------------------------------------------
# (2) Feed Query → LLM Synthesis
# ----------------------------------------------------------
@llm_bp.post("/query_feeds")
def query_feeds():
    ok, resp, code = guard()
    if not ok:
        return resp, code

    data      = request.json or {}
    query     = data.get("query", "").strip()
    persona   = data.get("persona", "chip").lower()
    model_in  = data.get("model", "auto")
    ln_mode   = data.get("latenight", False)

    stories  = load_rolling()
    clusters = load_clusters()

    cname, csum, signals = top_signals(query, stories, clusters)
    persona_data = apply_latenight_overrides(persona, load_persona(persona), ln_mode)

    model = select_model(model_in)
    prompt = build_prompt(persona, persona_data, signals)

    try:
        out = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=450
        )
        script = out.choices[0].message.content  # FIXED

        recommended = recommended_persona_for_signals(signals)
        warn = maybe_warn(persona, recommended)

        return jsonify({
            "ok": True,
            "persona": persona,
            "recommended_persona": recommended,
            "model_used": model,
            "cluster": cname,
            "cluster_summary": csum,
            "signals_used": signals,
            "script": script,
            "warning": warn
        })

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ----------------------------------------------------------
# (3) Queue Segment
# ----------------------------------------------------------
@llm_bp.post("/queue_segment")
def queue_segment():
    ok, resp, code = guard()
    if not ok:
        return resp, code

    data = request.json or {}
    entry = {
        "id": f"Q-{int(time.time())}",
        "persona": data.get("persona"),
        "script": data.get("script"),
        "domain": data.get("domain"),
        "created": time.time()
    }

    if not QUEUE_PATH.exists():
        QUEUE_PATH.write_text(json.dumps([entry], indent=2))
    else:
        content = json.loads(QUEUE_PATH.read_text())
        content.append(entry)
        QUEUE_PATH.write_text(json.dumps(content, indent=2))

    return jsonify({"ok": True, "message": "Queued for next episode."})


# ----------------------------------------------------------
# (4) StoryBank Save
# ----------------------------------------------------------
@llm_bp.post("/save_to_storybank")
def save_to_storybank():
    ok, resp, code = guard()
    if not ok:
        return resp, code

    data = request.json or {}
    entry = {
        "id": f"SB-{int(time.time())}",
        "persona": data.get("persona"),
        "script": data.get("script"),
        "domain": data.get("domain"),
        "tags": data.get("tags", []),
        "created": time.time()
    }

    if not STORYBANK_PATH.exists():
        STORYBANK_PATH.write_text(json.dumps({"segments": [entry]}, indent=2))
    else:
        content = json.loads(STORYBANK_PATH.read_text())
        content["segments"].append(entry)
        STORYBANK_PATH.write_text(json.dumps(content, indent=2))

    return jsonify({"ok": True, "message": "Saved to StoryBank."})

