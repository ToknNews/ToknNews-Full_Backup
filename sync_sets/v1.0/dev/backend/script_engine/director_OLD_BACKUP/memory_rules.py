# backend/script_engine/director/memory_rules.py

def evaluate_memory_callbacks(state, enriched_story):
    """
    Stub: checks if today's daily memory contains
    any keys that match parts of the headline.
    """

    callbacks = []

    headline = enriched_story.get("headline", "").lower()

    for key, value in state.daily_memory.items():
        if key.lower() in headline:
            callbacks.append(value)

    return callbacks
