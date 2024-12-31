from flask import Blueprint, jsonify

game_bp = Blueprint("game", __name__)

@game_bp.route("/status", methods=["GET"])
def game_status():
    return jsonify({"status": "Game in progress"})
