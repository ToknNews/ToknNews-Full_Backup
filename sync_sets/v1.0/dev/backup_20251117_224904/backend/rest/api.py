from fastapi import FastAPI
from rest.routes.health import router as health_router
from rest.routes.ingest import router as ingest_router
from rest.routes.compiler import router as compiler_router
from rest.routes.ingest_v2 import fetch_all, enrich, submit, run_cycle

app = FastAPI(title="ToknNews REST API")

app.include_router(health_router)
app.include_router(ingest_router)
app.include_router(compiler_router)
app.include_router(fetch_all.router)
app.include_router(enrich.router)
app.include_router(submit.router)
app.include_router(run_cycle.router)
