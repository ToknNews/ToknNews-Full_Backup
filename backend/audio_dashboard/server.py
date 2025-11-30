#!/usr/bin/env python3
import sys, os
sys.path.insert(0, "/var/www/toknnews-live/backend")

from flask import Flask, request, jsonify, send_file, render_template_string
import json, time

from script_engine.audio.tts_renderer import render_block
from script_engine.audio.mixer import mix_scene

# ---------------------------------------------------------
# DIRECTORIES
# ---------------------------------------------------------
AUDIO_DIR = "/var/www/toknnews/data/audio"
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

os.makedirs(AUDIO_DIR, exist_ok=True)

# Flask with static enabled
app = Flask(
    __name__,
    static_url_path="/static",
    static_folder=STATIC_DIR
)

# ---------------------------------------------------------
# STATIC FILES (CSS, Banner, Logo)
# ---------------------------------------------------------
@app.route('/static/<path:filename>')
def static_proxy(filename):
    return send_file(os.path.join(STATIC_DIR, filename))


# ---------------------------------------------------------
# HOMEPAGE — RENDERS THE TOKN UI + AUDIO LIST
# ---------------------------------------------------------
@app.route("/", methods=["GET"])
def index():
    files = sorted([
        f for f in os.listdir(AUDIO_DIR)
        if f.lower().endswith(".mp3") or f.lower().endswith(".wav")
    ])

    categories = {
        "Scenes": [],
        "Chip": [],
        "Anchors": [],
        "Vega": [],
        "Bitsy": [],
        "Other": []
    }

    for f in files:
        if f.startswith("scene_"):
            categories["Scenes"].append(f)
        elif f.startswith("chip_"):
            categories["Chip"].append(f)
        elif f.startswith(("lawson_", "reef_", "bond_")):
            categories["Anchors"].append(f)
        elif f.startswith("vega_"):
            categories["Vega"].append(f)
        elif f.startswith("bitsy_"):
            categories["Bitsy"].append(f)
        else:
            categories["Other"].append(f)

    audio_html = ""
    for cat, items in categories.items():
        if items:
            audio_html += f"<h2>{cat}</h2>"
            for item in items:
                audio_html += f'<div><a href="/audio/{item}">{item}</a></div>'

    # Load UI template
    with open(os.path.join(STATIC_DIR, "index.html")) as f:
        template = f.read()

    return render_template_string(template, audio_html=audio_html)


# ---------------------------------------------------------
# SERVE INDIVIDUAL AUDIO FILES
# ---------------------------------------------------------
@app.route("/audio/<path:filename>", methods=["GET"])
def serve_audio(filename):
    full_path = os.path.join(AUDIO_DIR, filename)
    if not os.path.exists(full_path):
        return {"error": "File not found"}, 404
    return send_file(full_path, mimetype="audio/mpeg")


# ---------------------------------------------------------
# RENDER SCENE (core audio generation)
# ---------------------------------------------------------
@app.route("/render_scene", methods=["POST"])
def render_scene():
    try:
        data = request.json
        scene_id = data["scene_id"]
        blocks = data["audio_blocks"]

        block_paths = []
        for blk in blocks:
            p = render_block(blk, scene_id)
            block_paths.append(p)

        final_audio = mix_scene(scene_id, block_paths)

        return jsonify({
            "status": "ok",
            "final_audio": final_audio
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ---------------------------------------------------------
# SIMPLE HEALTH CHECK
# ---------------------------------------------------------
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "time": time.time()})


# ---------------------------------------------------------
# RUN APP
# ---------------------------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8999)
