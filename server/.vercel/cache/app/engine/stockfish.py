import os
import logging
import subprocess
from config.config import Config

class StockfishEngine:
    def __init__(self):
        self.stockfish_path = self._find_stockfish()
        if not self.stockfish_path:
            raise FileNotFoundError("Stockfish not found in any known location")
        
        self._initialize_engine()

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
            raise

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
