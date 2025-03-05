import chess
import chess.engine


class ChessEngine:
    """Simple chess engine wrapper"""

    def __init__(self):
        self.board = chess.Board()

    def reset(self):
        self.board = chess.Board()

    def make_move(self, move_str):
        try:
            move = self.board.parse_uci(move_str)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except ValueError:
            return False
