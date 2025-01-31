from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import logging
from routes.game_routes import game_routes

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# Stockfish configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKFISH_PATH = os.path.join(BASE_DIR, "models", "stockfish-ubuntu-x86-64-avx2")

class StockfishEngine:
    def __init__(self):
        if not os.path.exists(STOCKFISH_PATH):
            raise FileNotFoundError(f"Stockfish not found at {STOCKFISH_PATH}")
            
        try:
            self.stockfish = subprocess.Popen(
                [STOCKFISH_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.send_command("uci")
            self.read_output_until("uciok")
        except Exception as e:
            raise Exception(f"Failed to start Stockfish: {str(e)}")

    def send_command(self, cmd):
        self.stockfish.stdin.write(f"{cmd}\n")
        self.stockfish.stdin.flush()

    def read_output_until(self, target):
        while True:
            line = self.stockfish.stdout.readline().strip()
            if target in line:
                return line

    def get_best_move(self, fen, skill_level=20):
        self.send_command(f"setoption name Skill Level value {skill_level}")
        self.send_command("ucinewgame")
        self.send_command(f"position fen {fen}")
        self.send_command("go movetime 1000")
        return self.read_output_until("bestmove").split()[1]

# Initialize Stockfish engine
try:
    engine = StockfishEngine()
    logging.info("Stockfish engine initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Stockfish engine: {str(e)}")
    engine = None

# Register blueprints
app.register_blueprint(game_routes, url_prefix='/api/game')

# Stockfish routes
@app.route('/api/stockfish/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok' if engine is not None else 'error',
        'stockfish_path': STOCKFISH_PATH,
        'stockfish_exists': os.path.exists(STOCKFISH_PATH)
    })

@app.route('/api/stockfish/move', methods=['POST'])
def get_move():
    if engine is None:
        return jsonify({'error': 'Stockfish engine not initialized'}), 500
        
    data = request.json
    if not data or 'fen' not in data:
        return jsonify({'error': 'FEN position is required'}), 400
        
    try:
        best_move = engine.get_best_move(data['fen'], data.get('skillLevel', 20))
        return jsonify({'move': best_move})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
