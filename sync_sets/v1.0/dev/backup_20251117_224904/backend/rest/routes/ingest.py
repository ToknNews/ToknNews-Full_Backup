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
    try:
        # Trigger the hybrid ingestor (main pipeline)
        subprocess.Popen(
            ["python3", "/var/www/toknnews-live/backend/live/hybrid_ingestor.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "started", "module": "hybrid_ingestor"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
