from fastapi import APIRouter
import subprocess
import json
import os

router = APIRouter(prefix="/compiler")

LATEST_SCENE_FILE = "/var/www/toknnews-live/data/latest_scene.json"

@router.get("/run")
def run_compiler():
    try:
        subprocess.Popen(
            ["python3", "/var/www/toknnews-live/backend/live/scene_compiler_live.py"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return {"status": "started", "module": "scene_compiler_live"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@router.get("/latest")
def latest_scene():
    try:
        if os.path.exists(LATEST_SCENE_FILE):
            with open(LATEST_SCENE_FILE, "r") as f:
                return json.load(f)
        return {"status": "none", "detail": "No scenes generated yet"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}
