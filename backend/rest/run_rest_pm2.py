#!/usr/bin/env python3
"""
ToknNews – Production REST Server (Waitress Entrypoint)
Runs the Flask app via Waitress on port 8800.
"""
from dotenv import load_dotenv
load_dotenv("/opt/toknnews/.env")

from waitress import serve
from backend.rest.api import app

from backend.rest.routes.moralis_webhook import moralis_webhook

from backend.rest.routes.moralis_verify import moralis_verify

from backend.toknclaw_proxy import toknclaw_bp
#--------------------------------------
# App Registration
#--------------------------------------


app.register_blueprint(moralis_webhook)
app.register_blueprint(moralis_verify)
app.register_blueprint(toknclaw_bp)

if __name__ == "__main__":
    print("Starting ToknNews REST API on port 8800...")
    serve(app, host="0.0.0.0", port=8800)
