from fastapi import APIRouter
import requests
import time

router = APIRouter(prefix="/ingest/v2")

BASE = "http://localhost:8800/ingest/v2"

@router.get("/run_cycle")
def run_cycle():
    items = requests.get(f"{BASE}/fetch_all").json()["items"]

    enriched = []
    for item in items:
        r = requests.post(f"{BASE}/enrich", json=item)
        enriched.append(r.json())

    submitted = []
    for e in enriched:
        r = requests.post(f"{BASE}/submit", json=e)
        submitted.append(r.json())

    return {
        "status": "complete",
        "fetched": len(items),
        "enriched": len(enriched),
        "submitted": len(submitted)
    }
