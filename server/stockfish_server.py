from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import logging

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.DEBUG)

# Try different possible stockfish paths
POSSIBLE_PATHS = [
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "stockfish-ubuntu-x86-64-avx2")
]

def find_stockfish():
    for path in POSSIBLE_PATHS:
        if os.path.exists(path):
            logging.info(f"Found Stockfish at: {path}")
            return path
        else:
            logging.warning(f"Stockfish not found at: {path}")
    return None

STOCKFISH_PATH = find_stockfish()
if not STOCKFISH_PATH:
    logging.error("Stockfish not found in any of the expected locations!")

class StockfishEngine:
    def __init__(self):
        if not STOCKFISH_PATH:
            raise FileNotFoundError("Stockfish not found! Please install Stockfish and ensure it's in PATH")
            
        try:
            logging.info(f"Attempting to start Stockfish from: {STOCKFISH_PATH}")
            self.stockfish = subprocess.Popen(
                [STOCKFISH_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            self.send_command("uci")
            response = self.read_output_until("uciok")
            logging.info(f"Stockfish initialized successfully: {response}")
        except Exception as e:
            logging.error(f"Failed to start Stockfish: {str(e)}")
            raise

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

# Initialize engine with better error handling
try:
    engine = StockfishEngine()
    logging.info("Stockfish engine initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Stockfish engine: {str(e)}")
    engine = None

@app.route('/health', methods=['GET'])
def health_check():
    status = {
        'status': 'ok' if engine is not None else 'error',
        'stockfish_path': STOCKFISH_PATH,
        'stockfish_exists': STOCKFISH_PATH and os.path.exists(STOCKFISH_PATH),
        'possible_paths': POSSIBLE_PATHS
    }
    logging.info(f"Health check: {status}")
    return jsonify(status)

@app.route('/get-move', methods=['POST'])
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

if __name__ == '__main__':
    logging.info("Starting Flask server...")
    app.run(port=5000, debug=True)
