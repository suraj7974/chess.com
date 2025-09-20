from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import sys

# Add the current directory to the path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Initialize with basic config first
from config.config import Config

def create_app():
    app = Flask(__name__)

    # Configure logging first
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Add request logging
    @app.before_request
    def log_request_info():
        logging.debug("Headers: %s", request.headers)
        logging.debug("URL: %s", request.url)
        logging.debug("Method: %s", request.method)

    # Configure CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)

    # Register blueprints
    from routes.stockfish_routes import stockfish_routes
    from routes.game_routes import game_routes
    from routes.groq_routes import groq_routes

    app.register_blueprint(stockfish_routes, url_prefix="/api/stockfish")
    app.register_blueprint(game_routes, url_prefix="/api/game")
    app.register_blueprint(groq_routes, url_prefix="/api/groq")

    @app.route("/favicon.ico")
    def favicon():
        return "", 204

    # Basic health check routes
    @app.route("/")
    def home():
        return jsonify({"message": "Chess game server is running", "status": "ok"})

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "message": "Server is healthy"})

    @app.route("/debug-info")
    def debug_info():
        return jsonify(
            {
                "env": Config.ENV,
                "debug": Config.DEBUG,
                "cors_origins": Config.CORS_ORIGINS,
                "python_version": sys.version,
                "current_dir": os.getcwd(),
                "python_path": sys.path,
                "registered_routes": [r.rule for r in app.url_map.iter_rules()],
            }
        )

    # List all registered routes for debugging
    @app.route("/routes")
    def list_routes():
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(
                {
                    "endpoint": rule.endpoint,
                    "methods": list(rule.methods),
                    "path": str(rule),
                }
            )
        return jsonify({"routes": routes})

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Unhandled exception: {str(e)}")
        return jsonify(
            {
                "status": "error",
                "message": "Internal server error",
                "details": str(e),
            }
        ), 500

    return app


app = create_app()



# For local development
if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Running in directory: {os.getcwd()}")
    print(f"Registered routes: {[r for r in app.url_map.iter_rules()]}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
