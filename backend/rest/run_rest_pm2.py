#!/usr/bin/env python3
"""
ToknNews – Production REST Server (Waitress Entrypoint)
Runs the Flask app via Waitress on port 8800.
"""

from waitress import serve
from api import app   # imports Flask app created in api.py

if __name__ == "__main__":
    print("Starting ToknNews REST API on port 8800...")
    serve(app, host="0.0.0.0", port=8800)
