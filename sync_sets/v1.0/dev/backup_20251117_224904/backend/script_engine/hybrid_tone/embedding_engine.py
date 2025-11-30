# backend/script_engine/hybrid_tone/embedding_engine.py

"""
A-16 Embedding Engine
Chip uses this to compute vector representations of headlines
for clustering, similarity detection, and narrative tracking.
"""

import os
import openai
import numpy as np

openai.api_key = os.getenv("OPENAI_API_KEY")

EMBED_MODEL = "text-embedding-3-small"   # fast + cheap

def embed_text(text: str):
    """
    Returns a numpy vector embedding for text.
    """
    try:
        resp = openai.embeddings.create(
            model=EMBED_MODEL,
            input=text
        )
        return np.array(resp.data[0].embedding)
    except Exception:
        return None


def cosine_sim(a, b):
    """
    Compute cosine similarity between two vectors.
    """
    if a is None or b is None:
        return 0.0
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
