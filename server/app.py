from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import sys

# Add the current directory to the path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.config import Config
from routes.stockfish_routes import stockfish_routes
from routes.game_routes import game_routes
from routes.groq_routes import groq_routes


def create_app():
    app = Flask(__name__)

    # Add request logging
    @app.before_request
    def log_request_info():
        logging.debug("Headers: %s", request.headers)
        logging.debug("Body: %s", request.get_data())
        logging.debug("URL: %s", request.url)

    # Configure CORS - use a simple wildcard approach for Vercel deployment
    CORS(
        app,
        resources={r"/*": {"origins": "*"}},
        supports_credentials=True,
        methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Origin", "Accept"]
    )

    # Add CORS headers to all responses - especially needed for error responses
    @app.after_request
    def after_request(response):
        # Add CORS headers to every response
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type, Authorization, Origin, Accept")
        response.headers.add("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        
        # Handle preflight OPTIONS requests specially
        if request.method == "OPTIONS":
            return response
            
        return response

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Register blueprints - ensure all are registered
    print("Registering blueprints...")
    app.register_blueprint(stockfish_routes, url_prefix="/api/stockfish")
    app.register_blueprint(game_routes, url_prefix="/api/game")
    app.register_blueprint(groq_routes, url_prefix="/api/groq")
    print("Blueprints registered")

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

    @app.errorhandler(404)
    def not_found(error):
        # Ensure CORS headers are set even in error responses
        response = jsonify({"error": "Not found"})
        return response, 404

    @app.errorhandler(500)
    def internal_error(error):
        # Ensure CORS headers are set even in error responses
        response = jsonify({"error": "Internal server error"})
        return response, 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Unhandled exception: {str(e)}")
        # Ensure CORS headers are set even in exception responses
        response = jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e),
        })
        return response, 500

    @app.route("/")
    def home():
        return jsonify({"message": "Chess game server is running"})

    @app.route("/debug-info")
    def debug_info():
        return jsonify(
            {
                "env": Config.ENV,
                "debug": Config.DEBUG,
                "cors_origins": Config.CORS_ORIGINS,
                "stockfish_paths": Config.STOCKFISH_PATHS,
            }
        )

    return app


app = create_app()

# Add this outside the function to help with debugging
if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Running in directory: {os.getcwd()}")
    print(f"Registered routes: {[r for r in app.url_map.iter_rules()]}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
