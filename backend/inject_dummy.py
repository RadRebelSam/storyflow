
import sqlite3
import json
import time

def inject_dummy():
    db_path = "cache.db"
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    # Create valid dummy data matching the new full structure
    dummy_data = {
        "meta": {
            "video_id": "dummy_vid_1",
            "title": "Test History Item for Deletion",
            "duration": 600,
            "url": "http://test.com"
        },
        "transcript": [],
        "analysis": {
            "summary": "This is a test.",
            "narrative_arc": [],
            "learning_moments": []
        }
    }
    
    key = f"test_key_{int(time.time())}"
    model = "gpt-test"
    
    c.execute("""
        INSERT OR REPLACE INTO analysis_cache (key, data, model) 
        VALUES (?, ?, ?)
    """, (key, json.dumps(dummy_data), model))
    
    conn.commit()
    conn.close()
    print("Injected dummy history item.")

if __name__ == "__main__":
    inject_dummy()
