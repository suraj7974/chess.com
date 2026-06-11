import logging
import os
import random
import re
import traceback

import chess
from config.config import Config
from config.models import DEFAULT_MODEL, get_model_by_key

# Kept for backwards compatibility with debug endpoints; no longer used to
# serve gameplay moves (caching by position made every game identical and
# could pin a fallback move forever).
GLOBAL_MOVE_CACHE = {}


def _heuristic_move(fen):
    """Generate a reasonable move without an LLM (captures > checks > random)."""
    try:
        board = chess.Board(fen)
        moves = list(board.legal_moves)
        if not moves:
            return None
        captures = [m for m in moves if board.is_capture(m)]
        checks = [m for m in moves if board.gives_check(m)]
        if captures:
            return random.choice(captures).uci()
        if checks:
            return random.choice(checks).uci()
        return random.choice(moves).uci()
    except Exception as e:
        logging.error(f"Error in heuristic move generation: {e}")
        return None


class MockGroqEngine:
    """Fallback engine used only when the Groq client cannot be initialized
    (e.g. missing GROQ_API_KEY)."""

    def __init__(self, model_key=None, *args, **kwargs):
        self.model_key = model_key or DEFAULT_MODEL
        self.model_config = get_model_by_key(self.model_key)
        self.model_id = self.model_config["id"]
        self.move_history = []
        logging.warning(
            "Initialized MockGroqEngine — moves will NOT come from a real model"
        )

    def get_move(self, fen, previous_moves=None, invalid_move=None):
        move = _heuristic_move(fen)
        if move:
            return {"move": move, "source": "fallback"}
        raise Exception("No legal moves available")

    def change_model(self, model_key):
        self.model_key = model_key
        self.model_config = get_model_by_key(model_key)
        self.model_id = self.model_config["id"]
        return True


class GroqEngine:
    # Per-request timeout passed to the Groq SDK. Vercel functions allow well
    # over this, so the model gets a real chance to answer before we fall back.
    REQUEST_TIMEOUT = 20.0
    MAX_ATTEMPTS = 2  # initial try + one retry with feedback about a bad move

    def __init__(self, model_key=None):
        try:
            logging.info("Initializing Groq engine...")

            api_key = os.getenv("GROQ_API_KEY") or getattr(Config, "GROQ_API_KEY", None)
            if not api_key:
                raise ValueError(
                    "GROQ_API_KEY not found in environment variables or Config"
                )

            self.model_key = model_key or DEFAULT_MODEL
            self.model_config = get_model_by_key(self.model_key)
            self.model_id = self.model_config["id"]

            from groq import Groq

            self.client = Groq(api_key=api_key, timeout=self.REQUEST_TIMEOUT)
            self.move_history = []

            logging.info(f"Groq engine initialized with model {self.model_id}")
        except Exception as e:
            logging.error(f"Failed to initialize Groq engine: {e}")
            traceback.print_exc()
            raise

    def change_model(self, model_key):
        self.model_key = model_key
        self.model_config = get_model_by_key(model_key)
        self.model_id = self.model_config["id"]
        logging.info(f"Changed model to: {self.model_id} ({model_key})")
        return True

    def _create_prompt(self, board, bad_move=None):
        """Build the prompt. Including the legal move list makes nearly every
        response a legal move, so games are actually played by the model."""
        legal_san = [board.san(m) for m in board.legal_moves]
        current_player = "White" if board.turn == chess.WHITE else "Black"

        system_message = (
            "You are a strong chess engine. Pick the best move for the side to "
            "move. Reply with ONE move in standard algebraic notation, exactly "
            "as it appears in the legal move list. No explanation, no extra text."
        )

        user_message = (
            f"Position (FEN): {board.fen()}\n"
            f"Board:\n{board}\n\n"
            f"You are playing {current_player}.\n"
            f"Legal moves: {', '.join(legal_san)}\n"
        )
        if bad_move:
            user_message += (
                f"\nYour previous answer '{bad_move}' was not a legal move. "
                "Choose one move from the legal move list."
            )
        user_message += "\nBest move:"

        return system_message, user_message

    def _call_groq(self, system_message, user_message):
        params = {
            "model": self.model_id,
            "messages": [
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message},
            ],
            "max_completion_tokens": self.model_config.get("max_tokens", 64),
            "temperature": self.model_config.get("temperature", 0.2),
        }
        # Per-model reasoning control (gpt-oss: low/medium/high, qwen3: none/default)
        effort = self.model_config.get("reasoning_effort")
        if effort:
            params["reasoning_effort"] = effort

        response = self.client.chat.completions.create(**params)
        content = response.choices[0].message.content or ""
        return content.strip()

    @staticmethod
    def _extract_move(raw, board):
        """Pull a legal move out of the model's reply. Accepts SAN or UCI,
        tolerates surrounding chatter and <think> blocks."""
        if not raw:
            return None
        # Strip reasoning blocks if a model inlines them
        text = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()

        # Candidate tokens: SAN like e4, Nf3, exd5, O-O, e8=Q+ or UCI like e2e4
        tokens = re.findall(
            r"\b(?:O-O-O|O-O|[KQRBN]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?|[a-h][1-8][a-h][1-8][qrbn]?)\b",
            text,
        )
        for token in tokens:
            # Try SAN first
            try:
                move = board.parse_san(token)
                if move in board.legal_moves:
                    return move
            except ValueError:
                pass
            # Then UCI
            try:
                move = chess.Move.from_uci(token.lower())
                if move in board.legal_moves:
                    return move
            except ValueError:
                pass
        return None

    def get_move(self, fen, previous_moves=None, invalid_move=None):
        """Ask the model for a move. Returns a dict:
        {"move": <uci>, "source": "groq"|"fallback", "raw": <model reply>}"""
        board = chess.Board(fen)
        if not list(board.legal_moves):
            raise Exception("No legal moves available")

        bad_move = None
        last_error = None
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                system_message, user_message = self._create_prompt(board, bad_move)
                raw = self._call_groq(system_message, user_message)
                logging.info(f"Raw reply from {self.model_id}: {raw!r}")

                move = self._extract_move(raw, board)
                if move:
                    return {"move": move.uci(), "source": "groq", "raw": raw}

                bad_move = raw[:50]
                logging.warning(
                    f"Attempt {attempt + 1}: no legal move in reply {raw!r}"
                )
            except Exception as e:
                last_error = e
                logging.error(f"Groq API error on attempt {attempt + 1}: {e}")

        # Model never produced a legal move (or API failed) — heuristic fallback
        logging.warning(f"Falling back to heuristic move (last error: {last_error})")
        fallback = _heuristic_move(fen)
        if fallback:
            return {"move": fallback, "source": "fallback"}
        raise Exception(f"Failed to get a move: {last_error}")
