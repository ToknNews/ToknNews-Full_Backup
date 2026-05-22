from fastapi import APIRouter
import subprocess

router = APIRouter(prefix="/ingest")

@router.get("/sources")
def list_sources():
    return {
        "sources": [
            "hybrid",
            "rss",
            "coindesk",
            "dexscreener",
            "pumpfun",
            "moralis",
            "reddit"
        ]
    }

@router.get("/run")
def run_ingest():
    return {
        "status": "disabled",
        "reason": "Legacy ingest_v1 disabled. Use ingest_v2 via admin or PM2."
    }
