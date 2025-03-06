from flask import Blueprint, request, jsonify
import logging
import os
import traceback
import chess
from engine.groq_engine import GroqEngine
from config.config import Config
from config.models import get_model_list, get_model_by_key, DEFAULT_MODEL
import sys
import datetime

groq_routes = Blueprint("groq", __name__)
engine = None


def get_engine(model_key=None):
    global engine
    if engine is None:
        try:
            engine = GroqEngine(model_key)
        except Exception as e:
            logging.error(f"Failed to initialize Groq engine: {str(e)}")
    elif model_key and engine.model_key != model_key:
        # Change model if a different one is requested
        try:
            engine.change_model(model_key)
        except Exception as e:
            logging.error(f"Failed to change Groq model: {str(e)}")
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
            return jsonify({"status": "ok"})
        return jsonify({"status": "error", "message": "Engine not initialized"}), 500
    except Exception as e:
        logging.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@groq_routes.route("/move", methods=["POST"])
def get_move():
    try:
        data = request.json
        if not data or "fen" not in data:
            return jsonify({"error": "Missing FEN position"}), 400

        # Get model key if provided
        model_key = data.get("model", DEFAULT_MODEL)

        # Get or initialize engine with the selected model
        engine = get_engine(model_key)
        if not engine:
            return jsonify({"error": "Groq engine not available"}), 503

        fen = data["fen"]
        previous_moves = data.get("previousMoves", [])

        # Validate FEN
        try:
            chess.Board(fen)
        except ValueError:
            return jsonify({"error": "Invalid FEN format"}), 400

        # Get the move from the Groq engine
        move = engine.get_move(fen, previous_moves)
        return jsonify(
            {
                "move": move,
                "model": engine.model_key,
                "modelName": engine.model_config["name"],
            }
        )
    except Exception as e:
        logging.error(f"Move calculation failed: {e}")
        return jsonify({"error": str(e)}), 500


@groq_routes.route("/test-connection", methods=["GET"])
def test_connection():
    """Test endpoint to check if Groq API is accessible"""
    try:
        # Get API key with better error messaging
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            logging.error("GROQ_API_KEY not found in environment variables")
            print("ERROR: Missing GROQ_API_KEY in environment variables")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "GROQ_API_KEY not found. Check server logs.",
                    }
                ),
                500,
            )

        # Get model from environment or use default
        model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
        logging.info(f"Using model: {model_name}")

        # Try logging a bit of the key for debugging (first 5 chars only)
        logging.info(f"Using API key starting with: {api_key[:5]}...")

        # Try to import groq
        try:
            from groq import Groq
        except ImportError:
            logging.error("Failed to import groq library")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Failed to import groq library. Is it installed?",
                    }
                ),
                500,
            )

        # Try to initialize the client
        try:
            client = Groq(api_key=api_key)
        except Exception as e:
            logging.error(f"Failed to initialize Groq client: {str(e)}")
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": f"Failed to initialize Groq client: {str(e)}",
                    }
                ),
                500,
            )

        # Simple test request with better error handling
        try:
            response = client.chat.completions.create(
                model=model_name,  # Use the model from environment
                messages=[{"role": "user", "content": "Hello!"}],
                max_tokens=10,
            )
            content = response.choices[0].message.content
            return jsonify(
                {
                    "status": "ok",
                    "message": "Groq API connection successful",
                    "response": content,
                }
            )
        except Exception as e:
            logging.error(f"API call failed: {str(e)}")
            return (
                jsonify({"status": "error", "message": f"API call failed: {str(e)}"}),
                500,
            )
    except Exception as e:
        logging.error(f"Test connection failed: {str(e)}")
        traceback.print_exc()
        return (
            jsonify(
                {"status": "error", "message": f"Test connection failed: {str(e)}"}
            ),
            500,
        )


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
            }
        )
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
