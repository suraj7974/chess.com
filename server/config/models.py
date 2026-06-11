"""
Groq model definitions and configuration

Model IDs must exist on GroqCloud — see https://console.groq.com/docs/models.
`reasoning_effort` is passed to the API when set; valid values differ per
model family (gpt-oss: low/medium/high, qwen3: none/default).
"""

GROQ_MODELS = {
    "llama70b": {
        "id": "llama-3.3-70b-versatile",
        "name": "LLaMA 3.3 (70B)",
        "max_tokens": 20,
        "temperature": 0.2,
        "description": "Meta's flagship 70B model — strong all-round play",
    },
    "gpt-oss-20b": {
        "id": "openai/gpt-oss-20b",
        "name": "GPT-OSS (20B)",
        "max_tokens": 2048,
        "temperature": 0.3,
        "reasoning_effort": "low",
        "description": "OpenAI's open-weight reasoning model — thinks before moving",
    },
    "qwen3-32b": {
        "id": "qwen/qwen3-32b",
        "name": "Qwen 3 (32B)",
        "max_tokens": 64,
        "temperature": 0.2,
        "reasoning_effort": "none",
        "description": "Alibaba's Qwen3 — fast, direct answers",
    },
}

# Default model to use
DEFAULT_MODEL = "llama70b"


def get_model_by_key(key):
    """Get model configuration by key"""
    return GROQ_MODELS.get(key, GROQ_MODELS[DEFAULT_MODEL])


def get_model_list():
    """Get list of available models"""
    return [
        {"key": key, "name": model["name"], "description": model["description"]}
        for key, model in GROQ_MODELS.items()
    ]
