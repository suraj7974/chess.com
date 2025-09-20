import os
import logging
import chess
import traceback
import sys
import random
import time
import threading
from ..config.config import Config
from ..config.models import get_model_list, get_model_by_key, DEFAULT_MODEL

# Global cache for moves across engine instances
GLOBAL_MOVE_CACHE = {}

class MockGroqEngine:
    """Mock engine for fallback in production when Groq is unavailable"""

    def __init__(self, *args, **kwargs):
        self.model_key = DEFAULT_MODEL
        self.model_config = get_model_by_key(DEFAULT_MODEL)
        self.model_id = self.model_config["id"]
        self.move_history = []
        logging.info("Initialized MockGroqEngine as fallback")

    def get_move(self, fen, previous_moves=None, invalid_move=None):
        """Return a simple move for testing"""
        try:
            # Check cache first
            cache_key = f"{fen}_{self.model_key}"
            if cache_key in GLOBAL_MOVE_CACHE:
                logging.info(f"Using cached move for position: {fen}")
                return GLOBAL_MOVE_CACHE[cache_key]

            # Generate a better move using basic heuristics
            board = chess.Board(fen)
            moves = list(board.legal_moves)
            if moves:
                # Prioritize captures and checks
                captures = [move for move in moves if board.is_capture(move)]
                checks = [move for move in moves if board.gives_check(move)]

                if captures:
                    selected_move = random.choice(captures)
                elif checks:
                    selected_move = random.choice(checks)
                else:
                    selected_move = random.choice(moves)

                move_uci = selected_move.uci()
                # Store in cache
                GLOBAL_MOVE_CACHE[cache_key] = move_uci
                return move_uci
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
    MAX_RESPONSE_TIME = 8  # Maximum seconds to wait for Groq API response before using fallback

    def __init__(self, model_key=None):
        try:
            # Print debug information
            logging.info("Initializing Groq engine...")

            # Get API key from environment or Config
            api_key = os.getenv("GROQ_API_KEY")
            if not api_key and hasattr(Config, "GROQ_API_KEY"):
                api_key = Config.GROQ_API_KEY

            logging.info(f"API key exists: {bool(api_key)}")

            # Check if we're running on Vercel
            self.is_vercel = os.getenv("VERCEL") == "1"
            logging.info(f"Running on Vercel: {self.is_vercel}")

            # Get model configuration
            self.model_key = model_key if model_key else DEFAULT_MODEL
            self.model_config = get_model_by_key(self.model_key)
            self.model_id = self.model_config["id"]

            logging.info(f"Using model: {self.model_id} ({self.model_key})")

            # Check API key
            if not api_key:
                logging.error("GROQ_API_KEY not found in environment variables or Config")
                raise ValueError("GROQ_API_KEY not found in environment variables or Config")

            # Import Groq library
            from groq import Groq

            logging.info("Successfully imported groq library")

            # Initialize client - only pass API key, no other parameters
            logging.info("Creating Groq client...")
            self.client = Groq(api_key=api_key)
            self.move_history = []

            # Rate limiting variables
            self.last_api_call = 0
            self.min_call_interval = 0.5  # reduced to speed up responses
            self.backoff_time = 1.0  # reduced initial backoff time
            self.max_backoff = 2.0  # reduced maximum backoff
            self.consecutive_errors = 0
            self.max_retries = 1  # reduce retries to speed up fallback

            logging.info(f"Groq engine initialized successfully with model {self.model_id}")

            # Skip test connection to save on API tokens
            logging.info("Skipping test connection to preserve API quota")

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

        # Simplified system message to reduce token count
        system_message = """You are a chess AI. Calculate the best move for the current player. Respond ONLY with a single chess move in standard algebraic notation (e.g., "e5", "Nf6"). No explanation."""

        # Determine whose turn it is
        current_player = "WHITE" if board.turn == chess.WHITE else "BLACK"

        user_message = f"Board position (you are {current_player}):\n\n{formatted_board}\n\nRespond with ONLY the best move."

        return system_message, user_message

    def _get_fallback_move(self, fen):
        """Generate a fallback move when API calls fail"""
        try:
            board = chess.Board(fen)
            moves = list(board.legal_moves)
            if moves:
                # Try to make a reasonable move
                captures = [move for move in moves if board.is_capture(move)]
                checks = [move for move in moves if board.gives_check(move)]

                if captures:
                    return random.choice(captures).uci()
                elif checks:
                    return random.choice(checks).uci()
                else:
                    return random.choice(moves).uci()
            return None
        except Exception as e:
            logging.error(f"Error in fallback move generation: {e}")
            return None

    def _call_groq_api(self, system_message, user_message, result_dict):
        """Call the Groq API in a separate thread with timeout handling"""
        try:
            # Get temperature from model config
            temperature = self.model_config.get("temperature", 0.2)

            response = self.client.chat.completions.create(
                model=self.model_id,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=10,
                temperature=temperature,
            )

            raw_move = response.choices[0].message.content.strip()
            logging.info(f"Raw move from Groq: {raw_move}")

            # Store result in the shared dictionary
            result_dict["move"] = raw_move
            result_dict["success"] = True
        except Exception as e:
            logging.error(f"Error in API call thread: {str(e)}")
            result_dict["error"] = str(e)
            result_dict["success"] = False

    def get_move(self, fen, previous_moves=None, invalid_move=None):
        """Get a move from the Groq API with caching and timeout handling"""
        # Check cache first to avoid unnecessary API calls
        cache_key = f"{fen}_{self.model_key}"
        if cache_key in GLOBAL_MOVE_CACHE:
            logging.info(f"Using cached move for position: {fen}")
            return GLOBAL_MOVE_CACHE[cache_key]

        # If running on Vercel with limited execution time, use optimized mode
        if self.is_vercel:
            logging.info("Using optimized mode for Vercel environment")
            # Vercel has limited execution time, so return fallback move quickly
            fallback_move = self._get_fallback_move(fen)
            if fallback_move:
                GLOBAL_MOVE_CACHE[cache_key] = fallback_move
                return fallback_move

        # Create prompt
        system_message, user_message = self._create_prompt(
            fen, previous_moves, invalid_move
        )

        # Apply rate limiting
        current_time = time.time()
        time_since_last_call = current_time - self.last_api_call

        if time_since_last_call < self.min_call_interval:
            sleep_time = self.min_call_interval - time_since_last_call
            logging.info(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_api_call = time.time()

        # Use threading with timeout to avoid hanging
        result_dict = {"success": False, "move": None, "error": None}
        api_thread = threading.Thread(
            target=self._call_groq_api,
            args=(system_message, user_message, result_dict)
        )
        api_thread.daemon = True
        api_thread.start()

        # Wait for thread to complete or timeout
        api_thread.join(timeout=self.MAX_RESPONSE_TIME)

        # Check if we got a result within the timeout period
        if api_thread.is_alive() or not result_dict["success"]:
            logging.warning(f"API call timed out or failed after {self.MAX_RESPONSE_TIME}s. Using fallback.")
            # Thread is still running or failed, use fallback move
            fallback_move = self._get_fallback_move(fen)
            if fallback_move:
                GLOBAL_MOVE_CACHE[cache_key] = fallback_move
                return fallback_move
            raise Exception(f"Failed to get move: {result_dict.get('error', 'Timeout')}")

        # Process the successful API response
        raw_move = result_dict["move"]

        # Clean and validate move
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

                # Convert to UCI format and cache it
                move_uci = chess_move.uci()
                GLOBAL_MOVE_CACHE[cache_key] = move_uci
                return move_uci
        except Exception:
            pass

        # If we get here, the move wasn't valid
        logging.warning("API returned an invalid move, using fallback")
        fallback_move = self._get_fallback_move(fen)
        if fallback_move:
            GLOBAL_MOVE_CACHE[cache_key] = fallback_move
            return fallback_move

        raise Exception("Failed to get a valid move")

    def _clean_move(self, raw_move):
        """Clean the move text from the LLM response."""
        # More aggressive cleaning to handle various formats
        clean_move = raw_move.lower()

        # Remove common prefixes/suffixes and phrases
        prefixes = [
            "i play",
            "my move is",
            "move:",
            "i choose",
            "black plays",
            "i'll play",
            "i will play",
            "best move is",
            "okay",
            "alright",
            "sure",
            "the move",
            "i recommend",
        ]

        for prefix in prefixes:
            if clean_move.startswith(prefix):
                clean_move = clean_move[len(prefix):].strip()

        # Remove any non-move text, punctuation, and extra spaces
        clean_move = clean_move.split(".")[0] if "." in clean_move else clean_move
        clean_move = clean_move.split(",")[0] if "," in clean_move else clean_move
        clean_move = clean_move.split(":")[0] if ":" in clean_move else clean_move
        clean_move = clean_move.split(" ")[0] if " " in clean_move else clean_move

        return clean_move.strip()
