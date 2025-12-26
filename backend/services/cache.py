import sqlite3
import json
import hashlib
import os
from typing import Optional, Dict, Any

DB_PATH = "cache.db"
PROMPT_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "prompt.md")

class CacheService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS analysis_cache (
                key TEXT PRIMARY KEY,
                data TEXT,
                model TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

    def _get_prompt_hash(self) -> str:
        """Reads prompt.md and returns its hash."""
        try:
            with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
                return hashlib.md5(f.read().encode()).hexdigest()
        except Exception:
            return "default_prompt"

    def _generate_key(self, input_data: str, model: str) -> str:
        """Generates a unique hash for the input (URL or Text), model, and PROMPT content."""
        prompt_hash = self._get_prompt_hash()
        content = f"{input_data}::{model}::{prompt_hash}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, input_data: str, model: str) -> Optional[Dict[str, Any]]:
        key = self._generate_key(input_data, model)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM analysis_cache WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        
        if row:
            print(f"Cache HIT for {key[:8]}...")
            try:
                return json.loads(row[0])
            except:
                return None
        print(f"Cache MISS for {key[:8]}...")
        return None

    def set(self, input_data: str, model: str, data: Dict[str, Any]):
        key = self._generate_key(input_data, model)
        json_data = json.dumps(data)
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            INSERT OR REPLACE INTO analysis_cache (key, data, model) 
            VALUES (?, ?, ?)
        """, (key, json_data, model))
        conn.commit()
        conn.close()
        print(f"Cache SAVED for {key[:8]}...")

    def get_history_list(self) -> list:
        """Retrieves listing of all cached analysis."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT key, data, model, timestamp FROM analysis_cache ORDER BY timestamp DESC")
        rows = c.fetchall()
        
        history = []
        for row in rows:
            key, data_str, model, timestamp = row
            try:
                data = json.loads(data_str)
                # Safely extract meta info
                meta = data.get("meta", {})
                title = meta.get("title", f"Analysis from {timestamp}")
                url = meta.get("url", "No URL")
                
                history.append({
                    "key": key,
                    "title": title,
                    "url": url,
                    "model": model,
                    "timestamp": timestamp
                })
            except:
                continue
                
        conn.close()
        return history

    def get_analysis_by_key(self, key: str) -> Optional[Dict[str, Any]]:
        """Retrieves full analysis by cache key."""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT data FROM analysis_cache WHERE key = ?", (key,))
        row = c.fetchone()
        conn.close()
        
        if row:
            try:
                return json.loads(row[0])
            except:
                return None
                return None
        return None

    def delete_keys(self, keys: list):
        """Deletes specific keys from the cache."""
        if not keys:
            return
        
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        # Dynamically build query placeholder
        placeholders = ','.join('?' for _ in keys)
        sql = f"DELETE FROM analysis_cache WHERE key IN ({placeholders})"
        c.execute(sql, tuple(keys))
        conn.commit()
        conn.close()
        print(f"Deleted {len(keys)} items from cache.")

# Singleton instance
cache_service = CacheService()
