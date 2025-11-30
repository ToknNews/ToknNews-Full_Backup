# backend/script_engine/hybrid_tone/cluster_engine.py

from .embedding_engine import embed_text, cosine_sim

def detect_story_cluster(current, recent_stories, similarity_threshold=0.83):
    """
    Returns cluster metadata:
    - cluster_strength
    - top_match
    - similarity_scores
    - cluster_line (Chip-ready)
    """

    current_vec = embed_text(current.get("headline", ""))

    similarities = []
    for s in recent_stories:
        vec = embed_text(s.get("headline", ""))
        score = cosine_sim(current_vec, vec)
        similarities.append((s, score))

    if not similarities:
        return {"cluster_line": "", "cluster_strength": 0}

    # Sort descending by similarity
    similarities.sort(key=lambda x: x[1], reverse=True)
    top_story, top_score = similarities[0]

    # Strong match → same evolving story
    if top_score >= similarity_threshold:
        line = (
            f"This continues a thread we’ve been following — "
            f"closely related to the earlier headline: "
            f"“{top_story.get('headline', '')}”."
        )
        return {
            "cluster_line": line,
            "cluster_strength": top_score
        }

    # Moderate similarity → related domain or theme
    if top_score >= 0.65:
        line = (
            f"There’s a thematic overlap with earlier coverage, "
            f"though this one expands the angle in a new direction."
        )
        return {
            "cluster_line": line,
            "cluster_strength": top_score
        }

    # Weak similarity → narrative break
    line = (
        f"This stands apart from the recent set — "
        f"a shift from earlier storylines."
    )

    return {
        "cluster_line": line,
        "cluster_strength": top_score
    }
