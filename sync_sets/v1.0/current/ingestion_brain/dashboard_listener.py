#!/usr/bin/env python3
"""
TOKNNews Dashboard Listener
FastAPI + WebSocket service that streams heartbeat, continuity, and compile data
to the dashboard frontend in real time.
"""

import os, json, time, asyncio
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

DATA_DIR = "/var/www/toknnews/data"
FILES = {
    "heartbeat": os.path.join(DATA_DIR, "heartbeat.json"),
    "continuity": os.path.join(DATA_DIR, "continuity_log.json"),
    "compile": os.path.join(DATA_DIR, "compile_log.jsonl"),
    "scene": os.path.join(DATA_DIR, "latest_scene_blocks.json")
}

app = FastAPI(title="TOKNNews Dashboard Listener", version="1.0")

# ---- allow dashboard to connect (adjust domains if needed)
origins = [
    "https://toknnews.com",
    "http://localhost",
    "http://127.0.0.1"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------
# REST endpoints
# ------------------------------------------------------------
def safe_load(path):
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r") as f:
            if path.endswith(".jsonl"):
                lines = f.readlines()[-50:]
                return [json.loads(l) for l in lines if l.strip()]
            return json.load(f)
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/heartbeat")
async def get_heartbeat():
    return JSONResponse(safe_load(FILES["heartbeat"]))

@app.get("/api/continuity")
async def get_continuity():
    return JSONResponse(safe_load(FILES["continuity"]))

@app.get("/api/compile-log")
async def get_compile():
    return JSONResponse(safe_load(FILES["compile"]))

@app.get("/api/latest-scene")
async def get_scene():
    return JSONResponse(safe_load(FILES["scene"]))

# ------------------------------------------------------------
# Aggregated System Stats (for dashboard summary)
# ------------------------------------------------------------
import statistics

@app.get("/api/system-stats")
async def get_system_stats():
    try:
        # Load heartbeat for uptime / status
        hb = safe_load(FILES["heartbeat"])
        compile_entries = safe_load(FILES["compile"]) or []
        continuity = safe_load(FILES["continuity"]) or []

        total_scenes = len(compile_entries)
        runtimes = [float(e.get("runtime", 0)) for e in compile_entries if e.get("runtime")]
        avg_runtime = round(statistics.mean(runtimes), 1) if runtimes else 0

        # Count sentiments from compile log
        sentiments = {"bullish": 0, "bearish": 0, "neutral": 0}
        for e in compile_entries:
            s = e.get("sentiment", "neutral").lower()
            if s in sentiments:
                sentiments[s] += 1
            else:
                sentiments["neutral"] += 1

        return {
            "status": hb.get("status", "unknown"),
            "uptime": hb.get("system_uptime", "—"),
            "total_scenes": total_scenes,
            "avg_runtime": avg_runtime,
            "sentiment_distribution": sentiments,
            "timestamp": hb.get("timestamp"),
        }
    except Exception as e:
        return {"error": str(e)}

# ------------------------------------------------------------
# WebSocket push
# ------------------------------------------------------------
class FileWatcher(FileSystemEventHandler):
    def __init__(self):
        self.last_sent = 0
    async def broadcast(self, websocket, data_type):
        await websocket.send_json({"type": data_type, "data": safe_load(FILES[data_type])})

@app.websocket("/ws/live")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    watcher = FileWatcher()
    observer = Observer()
    observer.schedule(watcher, DATA_DIR, recursive=False)
    observer.start()
    try:
        while True:
            # Push heartbeat every 10 s
            await watcher.broadcast(websocket, "heartbeat")
            await asyncio.sleep(10)
    except Exception:
        pass
    finally:
        observer.stop()
        observer.join()
        await websocket.close()
