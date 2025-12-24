import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("SUPER_MIND_API_KEY")
BASE_URL = os.getenv("BASE_URL", "https://space.ai-builders.com/backend/v1")

def test_ai():
    print(f"Testing AI Connection...")
    print(f"URL: {BASE_URL}")
    print(f"Model: gemini-2.5-pro") # Using the one that was failing

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "gemini-2.5-pro",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant. Output JSON."},
            {"role": "user", "content": "Say hello in JSON format like {'message': 'hello'}"}
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(f"{BASE_URL}/chat/completions", json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("Response Body:")
            print(response.text)
            try:
                data = response.json()
                content = data['choices'][0]['message']['content']
                print("\nContent:")
                print(content)
            except Exception as e:
                print(f"Failed to parse JSON content: {e}")
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Request Failed: {e}")

if __name__ == "__main__":
    test_ai()
