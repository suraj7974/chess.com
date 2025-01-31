from flask import Blueprint, jsonify, request
from engine.stockfish import StockfishEngine
import logging

stockfish_routes = Blueprint('stockfish', __name__)
engine = None

try:
    engine = StockfishEngine()
    logging.info("Stockfish engine initialized successfully")
except Exception as e:
    logging.error(f"Failed to initialize Stockfish engine: {str(e)}")

@stockfish_routes.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok' if engine is not None else 'error',
        'stockfish_path': engine.stockfish_path if engine else None,
        'stockfish_exists': engine is not None
    })

@stockfish_routes.route('/move', methods=['POST'])
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
