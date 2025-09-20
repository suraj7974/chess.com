from flask import Blueprint, request, jsonify
import logging
import os
import traceback
import chess
import random
from ..engine.groq_engine import GroqEngine, MockGroqEngine, GLOBAL_MOVE_CACHE
from ..config.config import Config
from ..config.models import get_model_list, get_model_by_key, DEFAULT_MODEL
import sys
import datetime
import time

groq_routes = Blueprint("groq", __name__)
engine = None
use_mock = False  # Flag to indicate if we're using mock engine

# Track request times to identify slow requests
request_times = {}

def get_engine(model_key=None):
    global engine
    if engine is None:
        logging.info("Initializing Groq engine...")
        try:
            engine = GroqEngine(model_key)
            logging.info("Successfully initialized Groq engine")
        except Exception as e:
            logging.error(f"Failed to initialize Groq engine: {str(e)}")
            return None
    elif model_key and engine.model_key != model_key:
        logging.info(f"Changing Groq engine model to {model_key}...")
        try:
            engine.change_model(model_key)
            logging.info("Successfully changed Groq engine model")
        except Exception as e:
            logging.error(f"Failed to change model: {str(e)}")
    return engine


@groq_routes.route("/models", methods=["GET"])
def list_models():
    """List available Groq models"""
    try:
        # Log that the endpoint was called
        logging.info("Models endpoint called")

        # Get models and log them
        models = get_model_list()
        logging.info(f"Retrieved {len(models)} models: {[m['key'] for m in models]}")

        # Return models
        response = {"models": models, "default": DEFAULT_MODEL}
        logging.info(f"Returning response: {response}")
        return jsonify(response)
    except Exception as e:
        logging.error(f"Error listing models: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@groq_routes.route("/health", methods=["GET"])
def health_check():
    try:
        engine = get_engine()
        if engine:
            # Include cache stats in health check
            cache_size = len(GLOBAL_MOVE_CACHE)
            return jsonify(
                {
                    "status": "ok",
                    "mode": "mock" if use_mock else "real",
                    "model": engine.model_key,
                    "cache_size": cache_size,
                    "is_vercel": os.environ.get('VERCEL') == '1'
                }
            )
        return jsonify({"status": "error", "message": "Engine not initialized"}), 500
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@groq_routes.route("/move", methods=["POST"])
def get_move():
    # Start timing the request
    start_time = time.time()

    try:
        # Log request received
        logging.info("Received move request")

        # Validate request data
        if not request.is_json:
            logging.error("Request is not JSON format")
            return jsonify({"error": "Request must be JSON format"}), 400

        data = request.get_json(silent=True)
        if not data:
            logging.error("Failed to parse JSON from request")
            return jsonify({"error": "Invalid JSON in request"}), 400

        if "fen" not in data:
            logging.error("Missing FEN position in request")
            return jsonify({"error": "Missing FEN position"}), 400

        # Extract request details for logging and caching
        fen = data["fen"]
        model_key = data.get("model", DEFAULT_MODEL)
        previous_moves = data.get("previousMoves", [])

        # Get or initialize engine with the selected model
        engine = get_engine(model_key)
        if not engine:
            logging.error("Groq engine not available")
            return jsonify({"error": "Groq engine not available"}), 503

        logging.info(f"Processing move for position: {fen}")

        # Validate FEN
        try:
            chess.Board(fen)
        except ValueError as e:
            logging.error(f"Invalid FEN format: {str(e)}")
            return jsonify({"error": "Invalid FEN format"}), 400

        try:
            # Get the move from the Groq engine with timeout handling
            move = engine.get_move(fen, previous_moves)
            logging.info(f"Engine returned move: {move}")

            # Calculate elapsed time for logging
            elapsed = time.time() - start_time
            logging.info(f"Request completed in {elapsed:.2f}s")

            # Return successful response
            return jsonify({
                "move": move,
                "model": engine.model_key,
                "modelName": engine.model_config["name"],
                "responseTime": elapsed
            })
        except Exception as e:
            logging.error(f"Error getting move from engine: {str(e)}")
            traceback.print_exc()
            return jsonify({"error": f"Engine error: {str(e)}"}), 500

    except Exception as e:
        # Catch-all for any unexpected errors
        elapsed = time.time() - start_time
        logging.error(f"Unexpected error in move endpoint ({elapsed:.2f}s): {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

def _is_valid_uci_move(move_str, fen):
    """Validate if a string is a valid UCI move for the given position"""
    try:
        board = chess.Board(fen)
        move = chess.Move.from_uci(move_str)
        return move in board.legal_moves
    except ValueError:
        return False
    except Exception as e:
        logging.error(f"Error validating move: {e}")
        return False


@groq_routes.route("/debug", methods=["GET"])
def debug_info():
    """Debug endpoint to check environment configuration"""
    try:
        # Test importing the groq library
        groq_import_success = False
        groq_error = None
        try:
            import groq

            groq_import_success = True
            groq_version = groq.__version__
        except Exception as e:
            groq_error = str(e)

        # Try to read API key directly
        direct_api_key = os.getenv("GROQ_API_KEY", "")
        masked_key = direct_api_key[:5] + "..." if direct_api_key else None

        # Get current python path and environment
        python_path = sys.executable
        python_version = sys.version
        current_dir = os.getcwd()

        return jsonify(
            {
                "api_key_exists": bool(os.getenv("GROQ_API_KEY")),
                "api_key_prefix": masked_key,
                "model": os.getenv("GROQ_MODEL", "mistral-7b-instruct"),
                "config_api_key_exists": bool(Config.GROQ_API_KEY),
                "env_vars": list(os.environ.keys()),
                "groq_import_success": groq_import_success,
                "groq_error": groq_error,
                "groq_version": groq_version if groq_import_success else None,
                "python_path": python_path,
                "python_version": python_version,
                "current_dir": current_dir,
                "server_timestamp": datetime.datetime.now().isoformat(),
                "cache_size": len(GLOBAL_MOVE_CACHE),
                "is_vercel": os.environ.get('VERCEL') == '1'
            }
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@groq_routes.route("/clear-cache", methods=["POST"])
def clear_cache():
    """Clear the move cache"""
    try:
        GLOBAL_MOVE_CACHE.clear()
        return jsonify({"status": "ok", "message": "Cache cleared successfully"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
