from flask import Flask, jsonify
from flask_cors import CORS
from routes.game_routes import game_routes

app = Flask(__name__)
CORS(app)

# Register blueprints
app.register_blueprint(game_routes, url_prefix='/api/game')

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/')
def home():
    return jsonify({'message': 'Chess game server is running'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
