from flask import Blueprint, request, jsonify
import logging
import os
import traceback
import chess
import sys
import datetime
import time

from engine.groq_engine import GroqEngine, MockGroqEngine, GLOBAL_MOVE_CACHE
from config.config import Config
from config.models import get_model_list, get_model_by_key, DEFAULT_MODEL

groq_routes = Blueprint("groq", __name__)
engine = None
use_mock = False


def get_engine(model_key=None):
    """Initialize the real Groq engine; fall back to the mock engine only if
    initialization fails (e.g. missing API key)."""
    global engine, use_mock
    if engine is None:
        try:
            engine = GroqEngine(model_key)
            use_mock = False
            logging.info("Successfully initialized Groq engine")
        except Exception as e:
            logging.error(f"Failed to initialize real Groq engine: {e}")
            logging.warning("Falling back to mock engine — set GROQ_API_KEY to fix this")
            try:
                engine = MockGroqEngine(model_key)
                use_mock = True
            except Exception as e2:
                logging.error(f"Failed to initialize any engine: {e2}")
                return None
    elif model_key and engine.model_key != model_key:
        try:
            engine.change_model(model_key)
        except Exception as e:
            logging.error(f"Failed to change model: {e}")
    return engine


@groq_routes.route("/models", methods=["GET"])
def list_models():
    """List available Groq models"""
    try:
        models = get_model_list()
        return jsonify({"models": models, "default": DEFAULT_MODEL})
    except Exception as e:
        logging.error(f"Error listing models: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@groq_routes.route("/health", methods=["GET"])
def health_check():
    try:
        eng = get_engine()
        if eng:
            return jsonify(
                {
                    "status": "ok",
                    "mode": "mock" if use_mock else "real",
                    "model": eng.model_key,
                    "is_vercel": os.environ.get("VERCEL") == "1",
                }
            )
        return jsonify({"status": "error", "message": "Engine not initialized"}), 500
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@groq_routes.route("/move", methods=["POST"])
def get_move():
    start_time = time.time()

    try:
        if not request.is_json:
            return jsonify({"error": "Request must be JSON format"}), 400

        data = request.get_json(silent=True)
        if not data:
            return jsonify({"error": "Invalid JSON in request"}), 400
        if "fen" not in data:
            return jsonify({"error": "Missing FEN position"}), 400

        fen = data["fen"]
        model_key = data.get("model", DEFAULT_MODEL)
        previous_moves = data.get("previousMoves", [])

        # Validate FEN before doing anything expensive
        try:
            board = chess.Board(fen)
        except ValueError:
            return jsonify({"error": "Invalid FEN format"}), 400
        if not list(board.legal_moves):
            return jsonify({"error": "No legal moves available in position"}), 400

        eng = get_engine(model_key)
        if not eng:
            return jsonify({"error": "Groq engine not available"}), 503

        logging.info(f"Processing move for position: {fen} with model {model_key}")

        try:
            result = eng.get_move(fen, previous_moves)
            move = result["move"]
            source = result.get("source", "mock" if use_mock else "groq")

            elapsed = time.time() - start_time
            logging.info(f"Request completed in {elapsed:.2f}s (source={source})")

            return jsonify(
                {
                    "move": move,
                    "model": eng.model_key,
                    "modelName": eng.model_config["name"],
                    "source": "mock" if use_mock else source,
                    "responseTime": elapsed,
                }
            )
        except Exception as e:
            logging.error(f"Error getting move from engine: {e}")
            traceback.print_exc()

            # Emergency fallback so the game can continue
            fallback_move = next(iter(board.legal_moves)).uci()
            elapsed = time.time() - start_time
            return jsonify(
                {
                    "move": fallback_move,
                    "model": model_key,
                    "modelName": get_model_by_key(model_key)["name"],
                    "source": "fallback",
                    "responseTime": elapsed,
                }
            )

    except Exception as e:
        elapsed = time.time() - start_time
        logging.error(f"Unexpected error in move endpoint ({elapsed:.2f}s): {e}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500


@groq_routes.route("/debug", methods=["GET"])
def debug_info():
    """Debug endpoint to check environment configuration"""
    try:
        groq_import_success = False
        groq_error = None
        groq_version = None
        try:
            import groq

            groq_import_success = True
            groq_version = groq.__version__
        except Exception as e:
            groq_error = str(e)

        direct_api_key = os.getenv("GROQ_API_KEY", "")
        masked_key = direct_api_key[:5] + "..." if direct_api_key else None

        return jsonify(
            {
                "api_key_exists": bool(os.getenv("GROQ_API_KEY")),
                "api_key_prefix": masked_key,
                "config_api_key_exists": bool(Config.GROQ_API_KEY),
                "groq_import_success": groq_import_success,
                "groq_error": groq_error,
                "groq_version": groq_version,
                "engine_mode": "mock" if use_mock else ("real" if engine else "uninitialized"),
                "python_version": sys.version,
                "current_dir": os.getcwd(),
                "server_timestamp": datetime.datetime.now().isoformat(),
                "is_vercel": os.environ.get("VERCEL") == "1",
            }
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
