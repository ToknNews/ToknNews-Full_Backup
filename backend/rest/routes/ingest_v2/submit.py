from fastapi import APIRouter
import subprocess
import json
import time
import os

router = APIRouter(prefix="/ingest/v2")

LIVE = "/var/www/toknnews-live/backend/live"

@router.post("/submit")
def submit_story(data: dict):
    """Send enriched story to the scene compiler."""
    try:
        # Write temp json
        path = f"/var/www/toknnews-live/data/pending_story.json"
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        # Trigger compiler
        subprocess.Popen(
            ["python3", f"{LIVE}/scene_compiler_live.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        return {"status": "ok", "submitted_id": data.get("id")}

    except Exception as e:
        return {"status": "error", "detail": str(e)}
