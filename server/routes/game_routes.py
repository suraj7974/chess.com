from flask import Blueprint, request, jsonify
from services.chess_engine import ChessEngine
from services.llm_integration import get_llm_move

game_routes = Blueprint('game_routes', __name__)
chess_engines = {'default': ChessEngine()}

@game_routes.route('/start-game', methods=['POST'])
def start_game():
    player_type = request.json['playerType']
    game_id = chess_engines['default'].start_game()
    return jsonify({'gameId': game_id, 'status': 'Game started with ' + player_type})

@game_routes.route('/make-move', methods=['POST'])
def make_move():
    data = request.json
    game_id = data['gameId']
    move = data['move']
    response = chess_engines['default'].make_move(game_id, move)
    return jsonify(response)
