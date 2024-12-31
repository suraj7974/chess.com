from flask import Flask
from flask_cors import CORS
from routes.game_routes import game_routes

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(game_routes)

if __name__ == '__main__':
    app.run(debug=True)
