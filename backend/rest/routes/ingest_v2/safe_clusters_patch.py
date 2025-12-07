import time
from backend.script_engine.analytics_cluster_gpt_diagnostics import generate_clusters

def safe_generate_clusters_with_backoff(stories):
    """
    GPT cluster runner with retry backoff:
      Attempt 1 → wait 3 seconds
      Attempt 2 → wait 8 seconds
      Attempt 3 → wait 20 seconds
    Guarantees a fallback result if GPT fails.
    """
    delays = [3, 8, 20]
    last_error = None

    for attempt, delay in enumerate(delays, start=1):
        print(f"[CLUSTERS] Attempt {attempt} starting in {delay}s…")
        time.sleep(delay)

        try:
            raw = generate_clusters(stories)
            return {
                "ts": time.time(),
                "clusters": raw.get("clusters", []),
                "source": raw.get("source", "gpt")
            }
        except Exception as e:
            last_error = str(e)
            print(f"[CLUSTERS] Attempt {attempt} FAILED → {last_error}")

    # All attempts failed → fail safely
    print("[CLUSTERS] All GPT attempts failed — fallback mode")
    return {
        "ts": time.time(),
        "clusters": [],
        "source": "gpt_failure",
        "error": last_error
    }
