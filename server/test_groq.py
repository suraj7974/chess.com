import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("=== GROQ API TEST SCRIPT ===")
print(f"Python version: {sys.version}")
print(f"Current directory: {os.getcwd()}")

# Check for API key
api_key = os.getenv("GROQ_API_KEY")
print(f"API key exists: {bool(api_key)}")
if api_key:
    print(f"API key starts with: {api_key[:5]}...")
else:
    print("API key not found in environment variables")
    print("Available environment variables:", list(os.environ.keys()))
    sys.exit(1)

# Get model name
model_name = os.getenv("GROQ_MODEL", "llama3-8b-8192")
print(f"Using model: {model_name}")

# Try importing groq
try:
    print("Attempting to import groq...")
    from groq import Groq

    print("✓ Successfully imported groq")
    print(f"Groq version: {getattr(Groq, '__version__', 'unknown')}")
except ImportError as e:
    print(f"✗ Failed to import groq: {e}")
    print("Try installing with: pip install groq")
    sys.exit(1)

# Try creating a client without proxies
try:
    print("Creating Groq client...")
    # Only pass the API key without any additional parameters
    client = Groq(api_key=api_key)
    print("✓ Successfully created Groq client")
except Exception as e:
    print(f"✗ Failed to create Groq client: {e}")
    sys.exit(1)

# List available models
try:
    print("\nListing available models...")
    models = client.models.list()
    print("Available models:")
    for model in models.data:
        print(f"- {model.id}")
except Exception as e:
    print(f"✗ Failed to list models: {e}")

# Try making a simple request
try:
    print("\nMaking test API request...")
    print(f"Using model: {model_name}")
    print("This may take a few seconds...\n")

    response = client.chat.completions.create(
        model=model_name,  # Use the model name from env
        messages=[{"role": "user", "content": "Say hello in one word."}],
        max_tokens=10,
        temperature=0,
    )

    content = response.choices[0].message.content.strip()
    print(f"✓ API response received: '{content}'")
    print("\n=== TEST SUCCESSFUL ===")
except Exception as e:
    print(f"✗ API request failed: {e}")
    sys.exit(1)
