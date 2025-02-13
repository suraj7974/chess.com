from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from config.config import Config
from routes.stockfish_routes import stockfish_routes
from routes.game_routes import game_routes


def create_app():
    app = Flask(__name__)

    # Add request logging
    @app.before_request
    def log_request_info():
        logging.debug("Headers: %s", request.headers)
        logging.debug("Body: %s", request.get_data())
        logging.debug("URL: %s", request.url)

    # Configure CORS for production
    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*",  # Temporarily allow all origins for testing
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization", "Origin", "Accept"],
                "expose_headers": ["Content-Type"],
                "supports_credentials": True,
                "send_wildcard": False,
            }
        },
    )

    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        origin = request.headers.get("Origin")
        if origin in Config.CORS_ORIGINS:
            response.headers.add("Access-Control-Allow-Origin", origin)
            response.headers.add(
                "Access-Control-Allow-Headers", "Content-Type,Authorization"
            )
            response.headers.add("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
            response.headers.add("Access-Control-Allow-Credentials", "true")
        return response

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    # Register blueprints
    app.register_blueprint(stockfish_routes, url_prefix="/api/stockfish")
    app.register_blueprint(game_routes, url_prefix="/api/game")

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Unhandled exception: {str(e)}")
        return (
            jsonify(
                {
                    "status": "error",
                    "message": "Internal server error",
                    "details": str(e),
                }
            ),
            500,
        )

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

# Remove debug flag for production
if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
