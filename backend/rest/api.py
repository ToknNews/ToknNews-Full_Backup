#!/usr/bin/env python3
"""
ToknNews REST API Loader
"""

from flask import Flask

# --- Core Blueprints ---
from backend.rest.routes.health import health_bp
from backend.rest.routes.ingest_v2.submit import ingest_v2_bp
from backend.rest.routes.admin import admin_bp
from backend.rest.routes.analytics import analytics_bp
from backend.rest.routes.analytics_refresh import refresh_bp
from backend.rest.routes.diagnostics_gpt import diagnostics_bp

# --- Studio Authentication ---
from backend.rest.routes.studio import studio_bp   # <-- the ONLY studio auth blueprint

def create_app():
    app = Flask(__name__)

    # Register routes
    app.register_blueprint(health_bp)
    app.register_blueprint(ingest_v2_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(refresh_bp)
    app.register_blueprint(diagnostics_bp)

    # Studio Login (Password + TOTP)
    app.register_blueprint(studio_bp)  # <-- FIXED

    return app


app = create_app()

if __name__ == "__main__":
    print("ToknNews API running on port 5599...")
    app.run(host="0.0.0.0", port=5599)
