from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import sys

# Add the current directory to the path to ensure imports work
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Initialize with basic config first
class BasicConfig:
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    IS_VERCEL = os.getenv("VERCEL") == "1"
    
    # Basic CORS configuration
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://chess-com-bay.vercel.app")
    CORS_ORIGINS = [
        FRONTEND_URL,
        "https://chess-com-bay.vercel.app",
        "https://chess-1uq742bpv-suraj-patels-projects-a4792e8b.vercel.app",
        "https://chessserver.vercel.app", 
        "http://localhost:5173",
        "http://localhost:5000",
        "http://localhost:3000",
        "*"  # Allow all for now to fix CORS
    ]
    
    PORT = int(os.getenv("PORT", 5000))
    HOST = "0.0.0.0"
    LOG_LEVEL = "INFO"

try:
    from config.config import Config
except ImportError as e:
    print(f"Config import error, using basic config: {e}")
    Config = BasicConfig

try:
    from routes.stockfish_routes import stockfish_routes
    from routes.game_routes import game_routes
    from routes.groq_routes import groq_routes
    routes_imported = True
except ImportError as e:
    print(f"Routes import error: {e}")
    print(f"Current directory: {current_dir}")
    print(f"Python path: {sys.path}")
    routes_imported = False


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

    # Configure CORS with simple, permissive settings
    CORS(
        app,
        origins="*",  # Allow all origins for now
        supports_credentials=True,
        methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Origin", "Accept", "X-Requested-With"]
    )

    # Simple CORS headers for all responses
    @app.after_request
    def after_request(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Origin, Accept, X-Requested-With"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    # Handle OPTIONS requests explicitly
    @app.before_request
    def handle_preflight():
        if request.method == "OPTIONS":
            response = jsonify({"status": "ok"})
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, Origin, Accept, X-Requested-With"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response

    # Register blueprints if they were imported successfully
    if routes_imported:
        print("Registering blueprints...")
        try:
            app.register_blueprint(stockfish_routes, url_prefix="/api/stockfish")
            app.register_blueprint(game_routes, url_prefix="/api/game")
            app.register_blueprint(groq_routes, url_prefix="/api/groq")
            print("Blueprints registered successfully")
        except Exception as e:
            print(f"Error registering blueprints: {e}")
    else:
        print("Routes not imported, creating basic endpoints")

    # Basic health check routes
    @app.route("/")
    def home():
        return jsonify({"message": "Chess game server is running", "status": "ok"})

    @app.route("/health")
    def health():
        return jsonify({"status": "ok", "message": "Server is healthy"})

    # Create basic groq health endpoint if routes not imported
    if not routes_imported:
        @app.route("/api/groq/health")
        def groq_health():
            return jsonify({
                "status": "ok", 
                "message": "Basic Groq endpoint",
                "mode": "fallback"
            })

    @app.route("/debug-info")
    def debug_info():
        return jsonify(
            {
                "env": Config.ENV,
                "debug": Config.DEBUG,
                "cors_origins": getattr(Config, 'CORS_ORIGINS', ['*']),
                "routes_imported": routes_imported,
                "is_vercel": getattr(Config, 'IS_VERCEL', False),
                "python_version": sys.version,
                "current_dir": os.getcwd()
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

    # Error handlers with CORS
    @app.errorhandler(404)
    def not_found(error):
        response = jsonify({"error": "Not found"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 404

    @app.errorhandler(500)
    def internal_error(error):
        response = jsonify({"error": "Internal server error"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500

    @app.errorhandler(Exception)
    def handle_exception(e):
        logging.error(f"Unhandled exception: {str(e)}")
        response = jsonify({
            "status": "error",
            "message": "Internal server error",
            "details": str(e),
        })
        response.headers["Access-Control-Allow-Origin"] = "*"
        return response, 500

    return app


app = create_app()

# WSGI handler for Vercel
def handler(request, context):
    return app

# For local development
if __name__ == "__main__":
    print(f"Python version: {sys.version}")
    print(f"Running in directory: {os.getcwd()}")
    print(f"Registered routes: {[r for r in app.url_map.iter_rules()]}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
