#!/usr/bin/env python3
"""
ToknNews REST API Loader
Primary entrypoint for Waitress via run_rest_pm2.py
"""

from flask import Flask

# --- Core Blueprints ---
from backend.rest.routes.health import health_bp
from backend.rest.routes.ingest_v2.submit import ingest_v2_bp
from backend.rest.routes.admin import admin_bp
from backend.rest.routes.analytics import analytics_bp
from backend.rest.routes.analytics_refresh import refresh_bp
from backend.rest.routes.diagnostics_gpt import diagnostics_bp
from backend.rest.routes.studio_ads import ads_bp
from backend.rest.routes.studio_episode import episode_bp

# --- Studio Authentication ---
from backend.rest.routes.studio import studio_bp

# --- NEW: Control Studio Panels ---
from backend.rest.routes.studio_control import control_bp

# --- NEW: LLM Tools ---
from backend.rest.routes.studio_llm import llm_bp


def create_app():
    app = Flask(__name__)

    # --- Register core routes ---
    app.register_blueprint(health_bp)
    app.register_blueprint(ingest_v2_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(refresh_bp)
    app.register_blueprint(diagnostics_bp)

    # --- Register Studio Auth ---
    app.register_blueprint(studio_bp)

    # --- Register Control Studio Panels ---
    app.register_blueprint(control_bp)

    # --- Register LLM Tools ---
    app.register_blueprint(llm_bp)
    app.register_blueprint(ads_bp)

    app.register_blueprint(episode_bp)

    return app


# Flask WSGI app (served by Waitress via run_rest_pm2.py)
app = create_app()


# Optional dev runner (ignored in production)
if __name__ == "__main__":
    print("ToknNews API running in development mode on port 5599...")
    app.run(host="0.0.0.0", port=5599)
