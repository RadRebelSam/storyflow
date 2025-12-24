import sqlite3
import json
import hashlib
import os
from typing import Optional, Dict, Any

DB_PATH = "cache.db"

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

    def _generate_key(self, input_data: str, model: str) -> str:
        """Generates a unique hash for the input (URL or Text) and model."""
        content = f"{input_data}::{model}"
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

# Singleton instance
cache_service = CacheService()
