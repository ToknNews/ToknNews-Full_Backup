import requests


OLLAMA_URL = "http://localhost:11434/api/generate"


def call_local_llm(prompt: str, model: str = "llama3:8b") -> str:
    try:
        r = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        r.raise_for_status()
        return r.json().get("response", "").strip()

    except Exception as e:
        raise RuntimeError(f"Local LLM error: {e}")
