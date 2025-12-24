import os
import requests
from dotenv import load_dotenv

# Create .env file for testing if it doesn't exist
if not os.path.exists('.env'):
    with open('.env', 'w') as f:
        f.write('SUPER_MIND_API_KEY=sk_1bd8fdf8_2f5d0a68763ad7c810cabf8aeb38fdbcca6d\n')

load_dotenv()

API_KEY = os.getenv("SUPER_MIND_API_KEY")
BASE_URL = "https://space.ai-builders.com/backend/v1"

def test_models():
    print("Testing Model List Endpoint...")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    try:
        response = requests.get(f"{BASE_URL}/models", headers=headers)
        if response.status_code == 200:
            print("SUCCESS: Retrieved models.")
            print(response.json())
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

def test_chat_completion():
    print("\nTesting Chat Completion...")
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    # Simple test payload
    payload = {
        "model": "gpt-4o", # Assuming gpt-4o is available, else we might need to pick from list
        "messages": [{"role": "user", "content": "Hello, are you working?"}]
    }
    
    try:
        response = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
        if response.status_code == 200:
            print("SUCCESS: Chat completion worked.")
            print(response.json())
        else:
            print(f"FAILED: Status {response.status_code}")
            print(response.text)
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_models()
    test_chat_completion()
