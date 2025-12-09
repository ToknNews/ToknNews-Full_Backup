#!/usr/bin/env python3
# Correct production server for a Flask app
from waitress import serve
from api import app   # This imports your Flask instance

if __name__ == "__main__":
    # Waitress will serve Flask correctly on port 8800
    serve(app, host="0.0.0.0", port=8800)
