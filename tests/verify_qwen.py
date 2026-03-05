
import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

api_key = os.getenv("QWEN_API_KEY")
base_url = os.getenv("QWEN_BASE_URL")
models = [os.getenv("QWEN_MODEL"), os.getenv("QWEN_MODEL_2")]

print(f"API Key: {api_key[:4]}...{api_key[-4:] if api_key else 'None'}")
print(f"Base URL: {base_url}")
print(f"Models to test: {models}")

if not api_key:
    print("Error: QWEN_API_KEY not found in environment.")
    exit(1)

# Try multiple endpoints
endpoints_str = os.getenv("QWEN_ENDPOINTS", "").strip()
endpoints = [ep.strip() for ep in endpoints_str.split(',') if ep.strip()]

if not endpoints:
    print("Error: QWEN_ENDPOINTS not found or empty in environment.")
    exit(1)

for base_url in endpoints:
    if not base_url:
        continue
    
    print(f"\n--- Testing Base URL: {base_url} ---")
    
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        timeout=10.0 # Set a shorter timeout to avoid waiting too long
    )

    for model in models:
        if not model:
            continue
        print(f"Testing model: {model}...")
        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": "Hello, simply reply with 'API is working!'"}
                ]
            )
            print(f"Success! Response: {completion.choices[0].message.content}")
        except Exception as e:
            print(f"Failed to verify model {model} on {base_url}. Error: {e}")
