from flask import Blueprint, request, jsonify
from backend.services.social_post_service import post_to_x

social_bp = Blueprint("social_service", __name__, url_prefix="/api/social")

@social_bp.route("/post", methods=["POST"])
def post_social():
    data = request.json or {}

    text = data.get("text")
    platform = data.get("platform", "x")

    if not text:
        return jsonify({"ok": False, "error": "Missing text"}), 400

    if platform == "x":
        result = post_to_x(text)
        return jsonify(result)

    return jsonify({"ok": False, "error": "Unsupported platform"})
