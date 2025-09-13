import os
from dotenv import load_dotenv

# Load .env file if it exists
load_dotenv()


class Config:
    # Environment
    ENV = os.getenv("FLASK_ENV", "production")
    DEBUG = ENV == "development"
    
    # Vercel specific settings
    IS_VERCEL = os.getenv("VERCEL") == "1"

    # Paths
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Stockfish configuration - adapted for serverless
    if IS_VERCEL:
        # On Vercel, use fallback chess logic instead of Stockfish binary
        STOCKFISH_PATHS = []
    else:
        STOCKFISH_PATHS = [
            os.path.join(BASE_DIR, "models", "stockfish-ubuntu-x86-64-avx2"),
            "/usr/games/stockfish",
            "/usr/bin/stockfish",
            "/usr/local/bin/stockfish",
            "stockfish",  # If in PATH
        ]

    # LLM API settings
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama3")

    # Server configuration
    PORT = int(os.getenv("PORT", 5000))
    HOST = "0.0.0.0"
    LOG_LEVEL = "INFO" if IS_VERCEL else ("DEBUG" if DEBUG else "INFO")

    # CORS settings - use environment variable if available
    FRONTEND_URL = os.getenv("FRONTEND_URL", "https://chess-com-bay.vercel.app")
    
    CORS_ORIGINS = [
        FRONTEND_URL,
        "https://chess-com-bay.vercel.app",
        "https://chess-1uq742bpv-suraj-patels-projects-a4792e8b.vercel.app",  # Alternative frontend URL
        "https://chessserver.vercel.app", 
        "http://localhost:5173",
        "http://localhost:5000",
        "http://localhost:3000",
    ]
    
    # If in development or no specific frontend URL, allow all
    if DEBUG or not os.getenv("FRONTEND_URL"):
        CORS_ORIGINS.append("*")
