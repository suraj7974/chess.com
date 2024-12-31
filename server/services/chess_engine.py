import chess
import chess.engine

class ChessEngine:
    def __init__(self):
        self.games = {}

    def start_game(self):
        game_id = len(self.games) + 1
        self.games[game_id] = chess.Board()
        return game_id

    def make_move(self, game_id, move):
        board = self.games.get(game_id)
        if not board:
            return {'error': 'Invalid game ID'}
        try:
            board.push_san(move)
            return {'board': board.fen(), 'status': 'Move made'}
        except ValueError:
            return {'error': 'Invalid move'}
