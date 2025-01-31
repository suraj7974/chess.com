import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    STOCKFISH_PATHS = [
        os.path.join(BASE_DIR, "models", "stockfish-ubuntu-x86-64-avx2"),
        "/usr/games/stockfish",
        "/usr/local/bin/stockfish",
        "stockfish"
    ]
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('FLASK_ENV') == 'development'
    LOG_LEVEL = 'DEBUG' if DEBUG else 'INFO'
