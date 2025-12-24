import requests
import time

def test_analyze_endpoint():
    url = "http://localhost:8000/analyze"
    
    # Use a short video for testing to be fast
    # Example: A short TED talk or similar. 
    # Or keep the one we have if it's not too long.
    payload = {
        "url": "https://www.youtube.com/watch?v=mock_video_id", # Triggers mock mode
        "model": "gemini-2.5-pro"
    }
    
    try:
        start_time = time.time()
        print(f"Sending analysis request to {url}...")
        response = requests.post(url, json=payload, timeout=300) # 5 min timeout
        
        if response.status_code == 200:
            data = response.json()
            print("\nSUCCESS: Analysis verification passed!")
            print(f"Title: {data['meta']['title']}")
            print(f"Duration: {data['meta']['duration']}s")
            print(f"Summary: {data['analysis'].get('summary')}")
            print(f"Arc Phases: {len(data['analysis'].get('narrative_arc', []))}")
            print(f"Learning Moments: {len(data['analysis'].get('learning_moments', []))}")
        else:
            print(f"FAILED: {response.status_code}")
            print(response.text)
            
        print(f"Total Time: {time.time() - start_time:.2f}s")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    test_analyze_endpoint()
