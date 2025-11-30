# backend/script_engine/hybrid_tone/consensus_engine.py

def compute_story_consensus(recent_stories, current_story):
    """
    Computes broad consensus sentiment & domain trend from recent stories.
    Returns a brief line Chip can inject into his commentary.
    """

    if not recent_stories or len(recent_stories) < 2:
        return ""

    # Extract story-level features
    sentiments = []
    domains = []
    importances = []

    for s in recent_stories:
        sentiments.append(s.get("sentiment", "neutral"))
        domains.append(s.get("domain", "general"))
        importances.append(s.get("importance", 5))

    # Compute dominant signals
    from collections import Counter
    dominant_sent = Counter(sentiments).most_common(1)[0][0]
    dominant_domain = Counter(domains).most_common(1)[0][0]
    avg_importance = sum(importances) / len(importances)

    line_parts = []

    # Consensus sentiment trend
    if dominant_sent == "positive":
        line_parts.append("Most of today’s flow has leaned risk-on")
    elif dominant_sent == "negative":
        line_parts.append("The broader backdrop has been risk-off")
    else:
        line_parts.append("Overall sentiment tonight has been mixed")

    # Domain clustering
    if dominant_domain in ["ai", "tech", "venture"]:
        line_parts.append("with AI/tech continuing to dominate the tape.")
    elif dominant_domain in ["markets", "macro"]:
        line_parts.append("with macro and liquidity still in the driver’s seat.")
    elif dominant_domain in ["defi", "onchain"]:
        line_parts.append("with on-chain activity setting much of the tone.")
    else:
        line_parts.append("across a pretty wide mix of topics.")

    consensus_line = " ".join(line_parts)

    # Detect divergence between consensus and the current story
    c_sent = current_story.get("sentiment")
    if c_sent and c_sent != dominant_sent:
        consensus_line += " This headline *breaks that pattern* and moves in the opposite direction."

    return consensus_line
