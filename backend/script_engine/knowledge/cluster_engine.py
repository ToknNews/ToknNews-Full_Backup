import time
from backend.script_engine.utils.story_lake import SHARDS, _load

CLUSTER_WINDOW_SECONDS = 6 * 3600  # 6 hours


def cluster_all_sources():
    """
    Cluster related stories across GPT, on-chain, and RSS.
    Returns list of clusters.
    """

    now = time.time()

    onchain = _load(SHARDS["onchain"])
    rss = _load(SHARDS["rss"])
    gpt = _load(SHARDS["gpt"])

    clusters = []

    for oc in onchain:
        cluster = {
            "primary_id": oc.get("tx_hash"),
            "domain": oc.get("domain"),
            "timestamp": oc.get("timestamp"),
            "onchain": oc,
            "rss": [],
            "gpt": [],
        }

        # Attach RSS context
        for r in rss:
            if abs(r.get("timestamp", 0) - oc.get("timestamp", 0)) > CLUSTER_WINDOW_SECONDS:
                continue

            if oc.get("token") and oc["token"] in (r.get("headline", "") + r.get("summary", "")):
                cluster["rss"].append(r)

        # Attach GPT narratives
        for g in gpt:
            if abs(g.get("timestamp", 0) - oc.get("timestamp", 0)) > CLUSTER_WINDOW_SECONDS:
                continue

            if oc.get("tx_hash") in g.get("supporting_ids", []):
                cluster["gpt"].append(g)

        clusters.append(cluster)

    return clusters
