from flask import Blueprint, jsonify

game_routes = Blueprint("game", __name__)


@game_routes.route("/start-game", methods=["POST"])
def start_game():
    return jsonify({"status": "ok", "gameId": "12345"})


@game_routes.route("/make-move", methods=["POST"])
def make_move():
    return jsonify({"success": True})


@game_routes.route("/test", methods=["GET"])
def test_route():
    return jsonify({"message": "Game routes working!"})
