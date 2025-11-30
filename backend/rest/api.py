#!/usr/bin/env python3
"""
ToknNews REST API – Minimal Stable Version (2025)

We no longer expose ingestion endpoints in REST.
Ingestion runs internally through PM2.

REST API now exposes:
 - /health
Future:
 - /status
 - /version
"""

from fastapi import FastAPI
from backend.rest.routes.health import router as health_router

app = FastAPI(title="ToknNews REST API")

# -------------------------------------------------
# Routers
# -------------------------------------------------
app.include_router(health_router)

# -------------------------------------------------
# Optional future expansion:
#   - status_router
#   - metrics_router
#   - episode_history_router
# -------------------------------------------------
