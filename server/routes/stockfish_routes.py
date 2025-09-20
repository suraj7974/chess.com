from flask import Blueprint, request, jsonify
from engine.stockfish import StockfishEngine
import logging

stockfish_routes = Blueprint("stockfish", __name__)

try:
    engine = StockfishEngine()
except Exception as e:
    logging.error(f"Failed to initialize Stockfish: {e}")
    engine = None


@stockfish_routes.route("/health", methods=["GET"])
def health_check():
    if engine:
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "Engine not initialized"}), 500


@stockfish_routes.route("/move", methods=["POST"])
def get_move():
    if not engine:
        return jsonify({"error": "Engine not available"}), 503

    data = request.get_json()
    if not data or "fen" not in data:
        return jsonify({"error": "Missing FEN position"}), 400

    fen = data["fen"]
    skill_level = data.get("skillLevel", 20)

    try:
        move = engine.get_best_move(fen, skill_level)
        return jsonify({"move": move})
    except Exception as e:
        logging.error(f"Move calculation failed: {e}")
        return jsonify({"error": str(e)}), 500
