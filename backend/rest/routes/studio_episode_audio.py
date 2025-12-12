#!/usr/bin/env python3
from flask import Blueprint, jsonify, send_file
import os

AUDIO_DIR = "/opt/toknnews/data/episodes"

audio_bp = Blueprint("audio_bp", __name__, url_prefix="/api/studio/episode")

@audio_bp.route("/audio/<episode_id>", methods=["GET"])
def get_audio(episode_id):

    # typical audio path
    audio_path = f"{AUDIO_DIR}/{episode_id}/final_audio.mp3"

    if not os.path.exists(audio_path):
        return jsonify({"ok": False, "error": "Audio not found"}), 404

    return send_file(audio_path, mimetype="audio/mpeg")
