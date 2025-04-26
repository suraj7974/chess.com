from flask import Blueprint, request, jsonify
import logging
import os
import traceback
import chess
from engine.groq_engine import GroqEngine, MockGroqEngine, GLOBAL_MOVE_CACHE
from config.config import Config
from config.models import get_model_list, get_model_by_key, DEFAULT_MODEL
import sys
import datetime
import time

groq_routes = Blueprint("groq", __name__)
engine = None
use_mock = False  # Flag to indicate if we're using mock engine

# Track request times to identify slow requests
request_times = {}

def get_engine(model_key=None):
    global engine, use_mock
    if engine is None:
        try:
            # Check if we're running on Vercel
            is_vercel = os.environ.get('VERCEL') == '1'
            
            # Default to mock engine on Vercel for reliability
            if is_vercel:
                logging.info("Running on Vercel - using MockGroqEngine for reliability")
                engine = MockGroqEngine(model_key)
                use_mock = True
            else:
                try:
                    # First try to initialize the real engine
                    engine = GroqEngine(model_key)
                    use_mock = False
                    logging.info("Successfully initialized Groq engine")
                except Exception as e:
                    # If that fails, fall back to the mock engine
                    logging.error(f"Failed to initialize real Groq engine: {str(e)}")
                    logging.info("Falling back to mock engine")
                    engine = MockGroqEngine(model_key)
                    use_mock = True
        except Exception as e:
            logging.error(f"Failed to initialize any engine: {str(e)}")
            return None
    elif model_key and engine.model_key != model_key:
        # Change model if a different one is requested
        try:
            engine.change_model(model_key)
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
        
        # Check if we have a cached move regardless of engine initialization
        # This helps avoid engine initialization if possible
        cache_key = f"{fen}_{model_key}"
        if cache_key in GLOBAL_MOVE_CACHE:
            cached_move = GLOBAL_MOVE_CACHE[cache_key]
            logging.info(f"Using cached move without engine initialization: {cached_move}")
            
            # Get basic model info without initializing engine
            model_config = get_model_by_key(model_key)
            model_name = model_config.get("name", model_key.capitalize())
            
            # Track request time
            elapsed = time.time() - start_time
            logging.info(f"Request completed in {elapsed:.2f}s (from cache)")
            
            return jsonify({
                "move": cached_move,
                "model": model_key,
                "modelName": model_name,
                "fromCache": True,
                "responseTime": elapsed
            })
        
        # Check if we're running on Vercel and need to be careful about timeouts
        is_vercel = os.environ.get('VERCEL') == '1'
        if is_vercel:
            # On Vercel, use a simpler approach to avoid timeouts
            logging.info("Running on Vercel - using simplified move generation")
            # Generate a basic move for Vercel without the full engine
            board = chess.Board(fen)
            moves = list(board.legal_moves)
            if moves:
                # Using basic strategy rather than full engine
                captures = [move for move in moves if board.is_capture(move)]
                checks = [move for move in moves if board.gives_check(move)]
                
                if captures:
                    simple_move = random.choice(captures).uci()
                elif checks:
                    simple_move = random.choice(checks).uci()
                else:
                    simple_move = random.choice(moves).uci()
                
                # Cache this move for future use
                GLOBAL_MOVE_CACHE[cache_key] = simple_move
                
                # Get basic model info without initializing engine
                model_config = get_model_by_key(model_key)
                model_name = model_config.get("name", model_key.capitalize())
                
                # Track request time
                elapsed = time.time() - start_time
                logging.info(f"Vercel request completed in {elapsed:.2f}s (simplified)")
                
                return jsonify({
                    "move": simple_move,
                    "model": model_key,
                    "modelName": model_name,
                    "simplified": True,
                    "responseTime": elapsed
                })
            else:
                logging.error("No legal moves available in position")
                return jsonify({"error": "No legal moves available in position"}), 400
                
        # For non-Vercel environments, continue with regular engine handling
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
            
            # Double-check that the move is valid
            if not _is_valid_uci_move(move, fen):
                logging.warning(f"Invalid move returned by engine: {move}")
                # Get a random valid move as fallback
                board = chess.Board(fen)
                if list(board.legal_moves):
                    move = list(board.legal_moves)[0].uci()
                    logging.info(f"Using fallback random move: {move}")
                    # Cache this move
                    GLOBAL_MOVE_CACHE[cache_key] = move
                else:
                    logging.error("No legal moves available")
                    return jsonify({"error": "No legal moves available in position"}), 400

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
            
            # Try to generate a simple valid move as emergency fallback
            try:
                board = chess.Board(fen)
                if list(board.legal_moves):
                    fallback_move = list(board.legal_moves)[0].uci()
                    logging.info(f"Using emergency fallback move after error: {fallback_move}")
                    GLOBAL_MOVE_CACHE[cache_key] = fallback_move
                    
                    # Return the fallback move
                    elapsed = time.time() - start_time
                    return jsonify({
                        "move": fallback_move,
                        "model": model_key,
                        "modelName": get_model_by_key(model_key)["name"],
                        "fallback": True,
                        "responseTime": elapsed
                    })
            except Exception:
                pass
                
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
