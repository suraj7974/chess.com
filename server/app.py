from flask import Flask, jsonify
from flask_cors import CORS
import logging
from config.config import Config
from routes.stockfish_routes import stockfish_routes
from routes.game_routes import game_routes


def create_app():
    app = Flask(__name__)

    # Configure CORS for production
    CORS(
        app,
        resources={
            r"/*": {
                "origins": Config.CORS_ORIGINS,
                "methods": ["GET", "POST", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            }
        },
    )

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

    @app.route("/")
    def home():
        return jsonify({"message": "Chess game server is running"})

    return app


app = create_app()

# Remove debug flag for production
if __name__ == "__main__":
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
