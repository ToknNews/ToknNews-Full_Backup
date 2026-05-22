#!/usr/bin/env python3
"""
ToknNews REST API Loader
Primary entrypoint for Waitress via run_rest_pm2.py

NOTE:
- Deprecated / experimental blueprints are intentionally NOT loaded
- Re-entry points for LLM tools and Ads are preserved as comments
"""

from flask import Flask

# -----------------------------------------------------------
# CORE SYSTEM BLUEPRINTS (STABLE)
# -----------------------------------------------------------
from backend.rest.routes.health import health_bp
from backend.rest.routes.ingest_v2.submit import ingest_v2_bp
from backend.rest.routes.admin import admin_bp
from backend.rest.routes.analytics import analytics_bp
from backend.rest.routes.studio_episode import episode_bp
from backend.rest.routes.studio_episode_audio import audio_bp

# -----------------------------------------------------------
# STUDIO AUTH + CONTROL (ACTIVE)
# -----------------------------------------------------------
from backend.rest.routes.studio import studio_bp
from backend.rest.routes.studio_control import control_bp

# -----------------------------------------------------------
# ADMIN LOGS (SAFE)
# -----------------------------------------------------------
from backend.rest.routes.admin_logs import admin_logs_bp

# -----------------------------------------------------------
# FUTURE / DEFERRED MODULES
# -----------------------------------------------------------
# LLM one-off generators (promo spots, character scripts)
# from backend.rest.routes.studio_llm import llm_bp

# Ads manager (future injection system)
# from backend.rest.routes.studio_ads import ads_bp

# Analytics refresh (currently deprecated OpenAI import path)
# from backend.rest.routes.analytics_refresh import refresh_bp


# -----------------------------------------------------------
# APPLICATION FACTORY
# -----------------------------------------------------------

def create_app():
    app = Flask(__name__)

    # -----------------------------
    # Core / Health / Ingest
    # -----------------------------
    app.register_blueprint(health_bp)
    app.register_blueprint(ingest_v2_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)

    # -----------------------------
    # Studio Auth + Control
    # -----------------------------
    app.register_blueprint(studio_bp)
    app.register_blueprint(control_bp)
    app.register_blueprint(episode_bp)

    # -----------------------------
    # Episode Audio (TTS access)
    # -----------------------------
    app.register_blueprint(audio_bp)

    # -----------------------------
    # Admin Logs
    # -----------------------------
    app.register_blueprint(admin_logs_bp)

    # -----------------------------
    # FUTURE (INTENTIONALLY DISABLED)
    # -----------------------------
    # app.register_blueprint(llm_bp)
    # app.register_blueprint(ads_bp)
    # app.register_blueprint(refresh_bp)

    return app


# -----------------------------------------------------------
# WSGI APP
# -----------------------------------------------------------

app = create_app()

if __name__ == "__main__":
    print("Do not run api.py directly — use run_rest_pm2.py")
