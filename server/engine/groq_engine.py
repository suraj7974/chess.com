import os
import logging
import chess
import traceback
import sys
from config.config import Config
from config.models import get_model_by_key, DEFAULT_MODEL


class MockGroqEngine:
    """Mock engine for fallback in production when Groq is unavailable"""

    def __init__(self, *args, **kwargs):
        self.model_key = DEFAULT_MODEL
        self.model_config = get_model_by_key(DEFAULT_MODEL)
        self.model_id = self.model_config["id"]
        self.move_history = []
        logging.info("Initialized MockGroqEngine as fallback")

    def get_move(self, fen, *args, **kwargs):
        """Return a simple move for testing"""
        try:
            # Get random legal move from position
            board = chess.Board(fen)
            moves = list(board.legal_moves)
            if moves:
                return moves[0].uci()
            return "e2e4"  # Default fallback move
        except Exception as e:
            logging.error(f"Error in mock engine: {e}")
            return "e2e4"

    def change_model(self, model_key):
        """Mock model change"""
        self.model_key = model_key
        self.model_config = get_model_by_key(model_key)
        self.model_id = self.model_config["id"]
        return True


class GroqEngine:
    def __init__(self, model_key=None):
        try:
            # Print debug information
            logging.info("Initializing Groq engine...")

            # Get API key
            api_key = os.getenv("GROQ_API_KEY")
            logging.info(f"API key exists: {bool(api_key)}")

            # Check if we're running on Vercel
            is_vercel = os.getenv("VERCEL") == "1"
            logging.info(f"Running on Vercel: {is_vercel}")

            # Get model configuration
            self.model_key = model_key if model_key else DEFAULT_MODEL
            self.model_config = get_model_by_key(self.model_key)
            self.model_id = self.model_config["id"]

            logging.info(f"Using model: {self.model_id} ({self.model_key})")

            # Check API key
            if not api_key:
                logging.error("GROQ_API_KEY not found in environment variables")
                # In production, try to get from Config
                if hasattr(Config, "GROQ_API_KEY") and Config.GROQ_API_KEY:
                    api_key = Config.GROQ_API_KEY
                    logging.info("Using API key from Config instead")
                else:
                    raise ValueError("GROQ_API_KEY not found in environment variables")

            # Import Groq library
            from groq import Groq

            logging.info("Successfully imported groq library")

            # Initialize client - only pass API key, no other parameters
            logging.info("Creating Groq client...")
            self.client = Groq(api_key=api_key)
            self.move_history = []

            # Test connection with simple query
            logging.info(f"Testing connection with model: {self.model_id}")

            test_response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )

            logging.info(
                f"Groq test response: {test_response.choices[0].message.content}"
            )
            logging.info(
                f"Groq engine initialized successfully with model {self.model_id}"
            )

        except Exception as e:
            logging.error(f"Failed to initialize Groq engine: {str(e)}")
            traceback.print_exc()
            raise

    def change_model(self, model_key):
        """Change the model being used"""
        self.model_key = model_key
        self.model_config = get_model_by_key(model_key)
        self.model_id = self.model_config["id"]
        logging.info(f"Changed model to: {self.model_id} ({model_key})")
        return True

    def _format_board(self, board):
        """Format the board for the LLM in an easy-to-understand way."""
        board_str = str(board)
        formatted = "\n".join(
            [f"{8-i}  {' '.join(board_str.split()[i*8:(i+1)*8])}" for i in range(8)]
        )
        formatted += "\n   a b c d e f g h"
        return formatted

    def _create_prompt(self, fen, move_history=None, invalid_move=None):
        """Create a prompt for the LLM with context about the game."""
        board = chess.Board(fen)
        formatted_board = self._format_board(board)

        system_message = """
        You are a chess grandmaster AI. Your task is to analyze the chess position shown below and suggest the best move for the side to play (BLACK).
        Return ONLY the move in standard algebraic notation (e.g., "e4", "Nf3", "Bxc6"). Do not explain your reasoning, don't include any other text.
        """

        user_message = f"Here is the current chess position (you are playing as BLACK):\n\n{formatted_board}\n\n"

        # Add move history
        if move_history and len(move_history) > 0:
            history_text = "Previous moves in this game:\n"
            for i, move in enumerate(move_history):
                history_text += f"{i+1}. {move}\n"
            user_message += f"{history_text}\n"

        # Add invalid move feedback
        if invalid_move:
            user_message += f"Your last move '{invalid_move}' was invalid. Please choose a legal move according to chess rules.\n"
            user_message += (
                "Legal moves from this position are: "
                + ", ".join([board.san(move) for move in board.legal_moves])
                + "\n"
            )

        user_message += "\nProvide your next move as BLACK:"

        return system_message, user_message

    def get_move(self, fen, previous_moves=None, invalid_move=None):
        """Get a move from the Groq API"""
        system_message, user_message = self._create_prompt(
            fen, previous_moves, invalid_move
        )

        try:
            logging.info(f"Sending request to Groq API with prompt: {user_message}")

            # Get temperature from model config
            temperature = self.model_config.get("temperature", 0.2)

            response = self.client.chat.completions.create(
                model=self.model_id,  # Use current model ID
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=10,
                temperature=temperature,
            )

            raw_move = response.choices[0].message.content.strip()
            logging.info(f"Raw move from Groq: {raw_move}")

            # Remove any non-move text and formatting
            clean_move = self._clean_move(raw_move)
            logging.info(f"Cleaned move: {clean_move}")

            # Validate the move
            board = chess.Board(fen)
            try:
                # Convert algebraic notation to a move
                chess_move = board.parse_san(clean_move)
                # Check if the move is legal
                if chess_move in board.legal_moves:
                    # Record the move in history
                    if previous_moves is not None:
                        self.move_history = previous_moves.copy()
                    self.move_history.append(clean_move)

                    # Convert to UCI format for consistency with stockfish
                    return chess_move.uci()
                else:
                    # If move isn't legal, try again with feedback
                    return self.get_move(fen, previous_moves, clean_move)
            except ValueError:
                # If the move can't be parsed, try again with feedback
                return self.get_move(fen, previous_moves, clean_move)

        except Exception as e:
            logging.error(f"Error getting move from Groq API: {str(e)}")
            raise

    def _clean_move(self, raw_move):
        """Clean the move text from the LLM response."""
        # Remove common prefixes/suffixes
        prefixes = ["I play", "My move is", "Move:", "I choose", "BLACK plays"]
        for prefix in prefixes:
            if raw_move.startswith(prefix):
                raw_move = raw_move[len(prefix) :].strip()

        # Remove punctuation and extra text
        raw_move = raw_move.split(".")[0] if "." in raw_move else raw_move
        raw_move = raw_move.split(",")[0] if "," in raw_move else raw_move

        return raw_move.strip()
