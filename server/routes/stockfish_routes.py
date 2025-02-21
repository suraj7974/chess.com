from flask import Blueprint, request, jsonify
from engine.stockfish import StockfishEngine
import logging

stockfish_routes = Blueprint("stockfish", __name__)
engine = None


def get_engine():
    global engine
    if engine is None:
        try:
            engine = StockfishEngine()
        except Exception as e:
            logging.error(f"Failed to initialize Stockfish: {e}")
    return engine


@stockfish_routes.route("/health", methods=["GET"])
def health_check():
    try:
        engine = get_engine()
        if engine:
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "message": "Engine not initialized"}), 500
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@stockfish_routes.route("/move", methods=["POST"])
def get_move():
    try:
        engine = get_engine()
        if not engine:
            return jsonify({"error": "Engine not available"}), 503

        data = request.get_json()
        if not data or "fen" not in data:
            return jsonify({"error": "Missing FEN position"}), 400

        fen = data["fen"]
        skill_level = data.get("skillLevel", 20)

        move = engine.get_best_move(fen, skill_level)
        return jsonify({"move": move})
    except Exception as e:
        logging.error(f"Move calculation failed: {e}")
        return jsonify({"error": str(e)}), 500
