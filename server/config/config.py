import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    # Environment
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Stockfish configuration
    STOCKFISH_PATHS = [
        os.path.join(BASE_DIR, "models", "stockfish-ubuntu-x86-64-avx2"),
        "/usr/games/stockfish",
        "/usr/bin/stockfish",
        "/usr/local/bin/stockfish",
        "stockfish",  # If in PATH
    ]

    # Server configuration
    PORT = int(os.getenv("PORT", 5000))
    HOST = "0.0.0.0"
    LOG_LEVEL = "DEBUG" if DEBUG else "INFO"

    # CORS settings (for production)
    CORS_ORIGINS = [
        "https://chess-com-bay.vercel.app",
        "http://localhost:5173",
        "http://localhost:5000",
    ]
