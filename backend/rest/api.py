#!/usr/bin/env python3
"""
ToknNews REST API Loader
Primary entrypoint for Waitress via run_rest_pm2.py
"""

from flask import Flask

# -----------------------------------------------------------
# CORE SYSTEM BLUEPRINTS
# -----------------------------------------------------------
from backend.rest.routes.health import health_bp
from backend.rest.routes.ingest_v2.submit import ingest_v2_bp
from backend.rest.routes.admin import admin_bp
from backend.rest.routes.analytics import analytics_bp
from backend.rest.routes.analytics_refresh import refresh_bp

# -----------------------------------------------------------
# STUDIO AUTH
# -----------------------------------------------------------
from backend.rest.routes.studio import studio_bp

# -----------------------------------------------------------
# CONTROL STUDIO v5 — EPISODE CONSOLE
# -----------------------------------------------------------
from backend.rest.routes.studio_control import control_bp

# -----------------------------------------------------------
# LLM TOOLS
# -----------------------------------------------------------
from backend.rest.routes.studio_llm import llm_bp

# -----------------------------------------------------------
# ADS MANAGER
# -----------------------------------------------------------
from backend.rest.routes.studio_ads import ads_bp

# -----------------------------------------------------------
# ADMIN LOGS
from backend.rest.routes.admin_logs import admin_logs_bp

# -----------------------------------------------------------
# EPISODE AUDIO
from backend.rest.routes.studio_episode_audio import audio_bp


# -----------------------------------------------------------
# APPLICATION FACTORY
# -----------------------------------------------------------

def create_app():
    app = Flask(__name__)

    # Core
    app.register_blueprint(health_bp)
    app.register_blueprint(ingest_v2_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(refresh_bp)

    # Auth
    app.register_blueprint(studio_bp)

    # Studio Console v5
    app.register_blueprint(control_bp)

    # LLM Tools + Ads
    app.register_blueprint(llm_bp)
    app.register_blueprint(ads_bp)

    # Admin Logs
    app.register_blueprint(admin_logs_bp)

    # EPISODE AUDIO
    app.register_blueprint(audio_bp)

    return app


# WSGI APP
app = create_app()


if __name__ == "__main__":
    print("ToknNews API running in development mode on port 5599…")
    app.run(host="0.0.0.0", port=5599)
