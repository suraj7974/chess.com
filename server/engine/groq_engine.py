import os
import logging
import chess
import traceback
import sys
import random
import time
from config.config import Config
from config.models import get_model_by_key, DEFAULT_MODEL


class MockGroqEngine:
    """Mock engine for fallback in production when Groq is unavailable"""

    def __init__(self, *args, **kwargs):
        self.model_key = DEFAULT_MODEL
        self.model_config = get_model_by_key(DEFAULT_MODEL)
        self.model_id = self.model_config["id"]
        self.move_history = []
        self.move_cache = {}  # Cache for previously generated moves
        logging.info("Initialized MockGroqEngine as fallback")

    def get_move(self, fen, previous_moves=None, invalid_move=None):
        """Return a simple move for testing"""
        try:
            # Check cache first
            cache_key = f"{fen}_{self.model_key}"
            if cache_key in self.move_cache:
                logging.info(f"Using cached move for position: {fen}")
                return self.move_cache[cache_key]
                
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
                self.move_cache[cache_key] = move_uci
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
            is_vercel = os.getenv("VERCEL") == "1"
            logging.info(f"Running on Vercel: {is_vercel}")

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
            
            # Cache for storing computed moves to avoid repeat API calls
            self.move_cache = {}
            
            # Rate limiting variables
            self.last_api_call = 0
            self.min_call_interval = 1.0  # seconds between API calls to avoid rate limiting
            self.backoff_time = 2.0  # initial backoff time in seconds
            self.max_backoff = 30.0  # maximum backoff time
            self.consecutive_errors = 0
            self.max_retries = 3

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

        # Improved system message with clearer instructions
        system_message = """
        You are a chess grandmaster AI analyzing chess positions. Your task is to calculate the best move for the current player in the given position.
        
        IMPORTANT: You must ONLY respond with a single chess move in standard algebraic notation (e.g., "e5", "Nf6", "Bxc6", "O-O").
        Do not include any explanation, discussion, or additional text whatsoever.
        Do not say words like "okay", "alright", "I'll play", etc.
        Just provide the move notation and nothing else.
        """

        # Determine whose turn it is
        current_player = "WHITE" if board.turn == chess.WHITE else "BLACK"
        
        user_message = f"Here is the current chess position (you are playing as {current_player}):\n\n{formatted_board}\n\n"

        # Add move history
        if move_history and len(move_history) > 0:
            history_text = "Previous moves in this game:\n"
            for i, move in enumerate(move_history):
                history_text += f"{i+1}. {move}\n"
            user_message += f"{history_text}\n"

        # Add invalid move feedback with explicit instructions
        if invalid_move:
            user_message += f"Your last move '{invalid_move}' was invalid. Choose a legal move from this list:\n"
            user_message += ", ".join([board.san(move) for move in board.legal_moves])
            user_message += "\n\nRespond with only one of these exact moves.\n"
        else:
            # Add a reminder to only output the move
            user_message += f"\nRespond with ONLY the best move for {current_player} using standard chess notation (like 'e5' or 'Nf6'). No other words."

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

    def get_move(self, fen, previous_moves=None, invalid_move=None):
        """Get a move from the Groq API with caching and retry logic"""
        # Check cache first to avoid unnecessary API calls
        cache_key = f"{fen}_{self.model_key}"
        if cache_key in self.move_cache:
            logging.info(f"Using cached move for position: {fen}")
            return self.move_cache[cache_key]
            
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
        
        # Retry logic for API calls
        retries = 0
        while retries <= self.max_retries:
            try:
                if retries > 0:
                    backoff = min(self.backoff_time * (2 ** (retries - 1)), self.max_backoff)
                    logging.info(f"Retry {retries}/{self.max_retries}: waiting {backoff:.2f} seconds")
                    time.sleep(backoff)
                
                logging.info(f"Sending request to Groq API (attempt {retries+1}/{self.max_retries+1})")
                self.last_api_call = time.time()

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

                # Reset consecutive errors counter on success
                self.consecutive_errors = 0

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
                        self.move_cache[cache_key] = move_uci
                        return move_uci
                    else:
                        # If this is the last retry, use a fallback move
                        if retries == self.max_retries:
                            fallback = self._get_fallback_move(fen)
                            if fallback:
                                self.move_cache[cache_key] = fallback
                                return fallback
                        
                        # Otherwise try again with feedback
                        retries += 1
                        continue
                except ValueError:
                    # If this is the last retry, use a fallback move
                    if retries == self.max_retries:
                        fallback = self._get_fallback_move(fen)
                        if fallback:
                            self.move_cache[cache_key] = fallback
                            return fallback
                    
                    # Otherwise try again with feedback
                    retries += 1
                    continue

            except Exception as e:
                logging.error(f"Error getting move from Groq API (attempt {retries+1}): {str(e)}")
                self.consecutive_errors += 1
                
                # If this is the last retry, use a fallback move
                if retries == self.max_retries:
                    fallback = self._get_fallback_move(fen)
                    if fallback:
                        # Cache the fallback move to avoid repeated failures
                        self.move_cache[cache_key] = fallback
                        return fallback
                    raise  # Re-raise the exception if we can't even get a fallback
                
                retries += 1
        
        # If we've exhausted retries and still don't have a move, try one more fallback
        fallback = self._get_fallback_move(fen)
        if fallback:
            self.move_cache[cache_key] = fallback
            return fallback
            
        raise Exception("Failed to get a valid move after multiple attempts")

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
