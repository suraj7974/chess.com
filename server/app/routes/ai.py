from flask import Blueprint, request, jsonify
import chess

ai_bp = Blueprint("ai", __name__)

@ai_bp.route("/move", methods=["POST"])
def ai_move():
    data = request.json
    fen = data.get("fen", "startpos")
    # For now, return a static move; integrate AI or Stockfish here.
    return jsonify({"move": "e2e4"})
