#!/usr/bin/env python3
"""
ToknNews V2 — Flask REST API Loader
"""

from flask import Flask

from backend.rest.routes.health import health_bp
from backend.rest.routes.ingest_v2.submit import ingest_v2_bp
from backend.rest.routes.admin import admin_bp
from backend.rest.routes.analytics import analytics_bp
from backend.rest.routes.studio_auth import studio_auth_bp
from backend.rest.routes.studio_auth import studio_auth_bp

# If you have analytics_refresh or others, re-add their imports and registrations.


def create_app():
    app = Flask(__name__)

    app.register_blueprint(health_bp)
    app.register_blueprint(ingest_v2_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(studio_auth_bp)
    app.register_blueprint(studio_auth_bp)

    return app


app = create_app()

if __name__ == "__main__":
    print("ToknNews V2 REST API starting on port 5599...")
    app.run(host="0.0.0.0", port=5599)
