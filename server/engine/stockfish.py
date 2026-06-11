import os
import logging
import subprocess
import random
import chess
from config.config import Config

class StockfishEngine:
    def __init__(self):
        self.is_serverless = self._check_serverless_env()
        self.stockfish_path = None
        
        if not self.is_serverless:
            self.stockfish_path = self._find_stockfish()
            if self.stockfish_path:
                self._initialize_engine()
            else:
                logging.warning("Stockfish binary not found. Using fallback mode.")
                self.is_serverless = True  # Force fallback mode
        else:
            logging.info("Running in serverless environment. Using fallback chess logic.")

    def _check_serverless_env(self):
        # Check if we're running in a serverless environment (like Vercel)
        return os.environ.get('VERCEL') == '1' or os.environ.get('AWS_LAMBDA_FUNCTION_NAME') is not None

    def _find_stockfish(self):
        for path in Config.STOCKFISH_PATHS:
            if os.path.exists(path):
                logging.info(f"Found Stockfish at: {path}")
                return path
        return None

    def _initialize_engine(self):
        try:
            os.chmod(self.stockfish_path, 0o755)
            self.stockfish = subprocess.Popen(
                [self.stockfish_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            self._setup_engine()
        except Exception as e:
            logging.error(f"Failed to initialize engine: {str(e)}")
            self.is_serverless = True  # Fall back to heuristic moves

    def _setup_engine(self):
        self.send_command("uci")
        self.read_output_until("uciok")
        self.send_command("setoption name Threads value 1")
        self.send_command("setoption name Hash value 64")

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

    def _get_fallback_move(self, fen):
        """Generate a valid chess move without using the Stockfish engine"""
        try:
            board = chess.Board(fen)
            legal_moves = list(board.legal_moves)
            if legal_moves:
                # Pick a reasonable move using basic heuristics
                captures = [move for move in legal_moves if board.is_capture(move)]
                checks = [move for move in legal_moves if board.gives_check(move)]
                
                # Prefer captures and checks, otherwise random move
                if captures:
                    selected_move = random.choice(captures)
                elif checks:
                    selected_move = random.choice(checks)
                else:
                    selected_move = random.choice(legal_moves)
                
                return selected_move.uci()
            return None
        except Exception as e:
            logging.error(f"Error in fallback move generation: {e}")
            return None

    def get_best_move(self, fen, skill_level=20):
        logging.info(f"Getting move for position: {fen}")
        
        # Use fallback mode in serverless environment
        if self.is_serverless:
            move = self._get_fallback_move(fen)
            logging.info(f"Fallback mode best move: {move}")
            return move
            
        # Traditional Stockfish mode for local environment
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
            logging.error(f"Error getting move, trying fallback: {str(e)}")
            # Fall back to simple move generation if the engine fails
            return self._get_fallback_move(fen)

    def __del__(self):
        if not self.is_serverless and hasattr(self, 'stockfish'):
            try:
                self.stockfish.terminate()
                self.stockfish.wait(timeout=1)
            except Exception as e:
                logging.error(f"Error cleaning up Stockfish: {str(e)}")
