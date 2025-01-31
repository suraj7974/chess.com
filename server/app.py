from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import logging
from routes.game_routes import game_routes

app = Flask(__name__)
CORS(app)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Stockfish configuration
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKFISH_PATH = os.path.join(BASE_DIR, "models", "stockfish-ubuntu-x86-64-avx2")

class StockfishEngine:
    def __init__(self):
        if not os.path.exists(STOCKFISH_PATH):
            logging.error(f"Stockfish not found at {STOCKFISH_PATH}")
            raise FileNotFoundError(f"Stockfish not found at {STOCKFISH_PATH}")
            
        try:
            # Make sure stockfish is executable
            os.chmod(STOCKFISH_PATH, 0o755)
            
            logging.info(f"Starting Stockfish from: {STOCKFISH_PATH}")
            self.stockfish = subprocess.Popen(
                [STOCKFISH_PATH],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Check if process is alive
            if self.stockfish.poll() is not None:
                raise Exception("Stockfish process failed to start")

            # Initialize engine
            self.send_command("uci")
            
            # Wait for initialization
            lines = []
            while True:
                line = self.stockfish.stdout.readline().strip()
                logging.debug(f"Init output: {line}")
                lines.append(line)
                if "uciok" in line:
                    break
                if not line and self.stockfish.poll() is not None:
                    raise Exception(f"Stockfish initialization failed: {'; '.join(lines)}")

            logging.info("Stockfish initialized successfully")
            
            # Set default options
            self.send_command("setoption name Threads value 1")
            self.send_command("setoption name Hash value 64")
            
        except Exception as e:
            logging.error(f"Failed to start Stockfish: {str(e)}")
            if hasattr(self, 'stockfish'):
                self.stockfish.terminate()
            raise

    def send_command(self, cmd):
        logging.debug(f"Sending command: {cmd}")
        try:
            self.stockfish.stdin.write(f"{cmd}\n")
            self.stockfish.stdin.flush()
        except Exception as e:
            logging.error(f"Error sending command: {str(e)}")
            raise

    def read_output_until(self, target):
        lines = []
        while True:
            if self.stockfish.poll() is not None:
                raise Exception(f"Stockfish process terminated: {'; '.join(lines)}")
                
            line = self.stockfish.stdout.readline().strip()
            logging.debug(f"Read output: {line}")
            lines.append(line)
            
            if target in line:
                return line

    def get_best_move(self, fen, skill_level=20):
        logging.info(f"Getting move for position: {fen}")
        try:
            self.send_command(f"setoption name Skill Level value {skill_level}")
            self.send_command("ucinewgame")
            self.send_command(f"position fen {fen}")
            self.send_command("go movetime 1000")
            
            result = self.read_output_until("bestmove")
            move = result.split()[1]
            logging.info(f"Best move found: {move}")
            return move
        except Exception as e:
            logging.error(f"Error getting move: {str(e)}")
            raise

    def __del__(self):
        if hasattr(self, 'stockfish'):
            try:
                self.stockfish.terminate()
                self.stockfish.wait(timeout=1)
            except Exception as e:
                logging.error(f"Error cleaning up Stockfish: {str(e)}")

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
