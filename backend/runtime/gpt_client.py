import os
import openai

# Ensure API key is loaded from environment
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not set in environment")

openai.api_key = OPENAI_API_KEY


class GPTClient:
    """
    Minimal GPT client for ToknNews ingestion.
    Provides a single .complete(prompt) interface.
    """

    def __init__(self, model="gpt-4o-mini"):
        self.model = model

    def complete(self, prompt: str) -> str:
        response = openai.ChatCompletion.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a precise market intelligence analyst."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=500,
        )
        return response.choices[0].message["content"]


def get_gpt_client():
    """
    Factory for GPT client.
    Centralized so we can swap models or providers later.
    """
    return GPTClient()
