"""
Groq model definitions and configuration
"""

# Available Groq models
GROQ_MODELS = {
    "deepseek": {
        "id": "deepseek-r1-distill-llama-70b",
        "name": "Deepseek R1 (70B)",
        "max_tokens": 4096,
        "temperature": 0.1,  # Lower temperature for more precise responses
        "description": "Powerful 70B model with excellent reasoning capabilities",
    },
    "mixtral": {
        "id": "mixtral-8x7b-32768",
        "name": "Mixtral 8x7B",
        "max_tokens": 8192,
        "temperature": 0.2,
        "description": "Strong mixture-of-experts model with long context",
    },
    "llama3": {
        "id": "llama-3.3-70b-versatile",
        "name": "LLaMa 3.3 (70B)",
        "max_tokens": 8192,
        "temperature": 0.2,
        "description": "Latest LLaMa model with versatile capabilities",
    },
    "gemma2": {
        "id": "gemma2-9b-it",
        "name": "Gemma 2 (9B)",
        "max_tokens": 4096,
        "temperature": 0.3,
        "description": "Smaller but efficient instruction-tuned model",
    },
}

# Default model to use
DEFAULT_MODEL = "llama3"


def get_model_by_key(key):
    """Get model configuration by key"""
    return GROQ_MODELS.get(key, GROQ_MODELS[DEFAULT_MODEL])


def get_model_list():
    """Get list of available models"""
    return [
        {"key": key, "name": model["name"], "description": model["description"]}
        for key, model in GROQ_MODELS.items()
    ]
