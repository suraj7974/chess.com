from flask import Flask

def create_app():
    app = Flask(__name__)

    # Import and register blueprints
    from .routes.game import game_bp
    from .routes.ai import ai_bp

    app.register_blueprint(game_bp, url_prefix="/api/game")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")

    @app.route("/")
    def home():
        return {"message": "Welcome to Chess Platform Backend!"}

    return app
