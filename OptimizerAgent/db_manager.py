import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

class DatabaseHandler:
    def __init__(self, db_name: str = "code_optimizer.db"):
        self.db_name = db_name
        self.init_database()
        self._connection = None
        self._cursor = None

    property
    def connection(self):
        if self._connection is None:
            self._connection = sqlite3.connect(self.db_name)
            self._connection.row_factory = sqlite3.Row
        return self._connection

    @property
    def cursor(self):
        if self._cursor is None:
            self._cursor = self.connection.cursor()
        return self._cursor

    def close(self):
        if self._cursor:
            self._cursor.close()
            self._cursor = None
        if self._connection:
            self._connection.close()
            self._connection = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Add indexes for better query performance
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    conversation_id INTEGER,
                    original_code TEXT NOT NULL,
                    num_techniques INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations (id) ON DELETE CASCADE
                )
            """)
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS optimization_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    entry_id INTEGER,
                    improved_code TEXT NOT NULL,
                    output TEXT,
                    execution_time FLOAT,
                    memory_usage FLOAT,
                    techniques TEXT,
                    FOREIGN KEY (entry_id) REFERENCES optimization_entries (id) ON DELETE CASCADE
                )
            """)
            
            # Add indexes
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversation_created 
                ON conversations(created_at)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_entries_conversation 
                ON optimization_entries(conversation_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_results_entry 
                ON optimization_results(entry_id)
            """)
            
            conn.commit()

    def execute_with_retry(self, query, params=None, max_retries=3):
        """Execute SQL with retry logic for better reliability"""
        for attempt in range(max_retries):
            try:
                if params is None:
                    self.cursor.execute(query)
                else:
                    self.cursor.execute(query, params)
                self.connection.commit()
                return self.cursor
            except sqlite3.OperationalError as e:
                if attempt == max_retries - 1:
                    raise
                time.sleep(0.1 * (attempt + 1))
                continue

    def create_conversation(self, title: str) -> int:
        """Create a new conversation and return its ID"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO conversations (title) VALUES (?)",
                (title,)
            )
            conn.commit()
            return cursor.lastrowid

    def save_optimization(self, conversation_id: int, original_code: str, 
                         num_techniques: int, results: List[Dict]) -> int:
        """Save optimization entry and its results"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            
            # Save optimization entry
            cursor.execute("""
                INSERT INTO optimization_entries 
                (conversation_id, original_code, num_techniques)
                VALUES (?, ?, ?)
            """, (conversation_id, original_code, num_techniques))
            
            entry_id = cursor.lastrowid
            
            # Save all results
            for result in results:
                cursor.execute("""
                    INSERT INTO optimization_results 
                    (entry_id, improved_code, output, execution_time, memory_usage, techniques)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entry_id,
                    result['code'],
                    result['output'],
                    result['execution_time'],
                    result['memory_usage'],  # Insert memory_usage
                    result['techniques']
                ))
            
            conn.commit()
            return entry_id

    def get_conversations(self) -> List[Dict]:
        """Get all conversations"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, title, created_at
                FROM conversations
                ORDER BY created_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]

    def get_conversation_entries(self, conversation_id: int) -> List[Dict]:
        """Get all entries for a specific conversation"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, original_code, num_techniques, created_at
                FROM optimization_entries
                WHERE conversation_id = ?
                ORDER BY created_at DESC
            """, (conversation_id,))
            return [dict(row) for row in cursor.fetchall()]

    def get_entry_results(self, entry_id: int) -> List[Dict]:
        """Get all results for a specific entry"""
        with sqlite3.connect(self.db_name) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT improved_code, output, execution_time, memory_usage, techniques
                FROM optimization_results
                WHERE entry_id = ?
            """, (entry_id,))
            return [dict(row) for row in cursor.fetchall()]
        
    def delete_conversation(self, conversation_id: int) -> None:
        """
        Delete a specific conversation and all its associated entries and results
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Get all entry IDs for this conversation
                cursor.execute(
                    "SELECT id FROM optimization_entries WHERE conversation_id = ?",
                    (conversation_id,)
                )
                entry_ids = [row[0] for row in cursor.fetchall()]
                
                # Delete all results for these entries
                for entry_id in entry_ids:
                    cursor.execute(
                        "DELETE FROM optimization_results WHERE entry_id = ?",
                        (entry_id,)
                    )
                
                # Delete all entries for this conversation
                cursor.execute(
                    "DELETE FROM optimization_entries WHERE conversation_id = ?",
                    (conversation_id,)
                )
                
                # Finally delete the conversation itself
                cursor.execute(
                    "DELETE FROM conversations WHERE id = ?",
                    (conversation_id,)
                )
                conn.commit()
        except Exception as e:
            print(f"Error deleting conversation: {e}")
            raise

    def clear_all_conversations(self) -> None:
        """
        Delete all conversations and their associated entries and results
        """
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                
                # Delete all results first
                cursor.execute("DELETE FROM optimization_results")
                
                # Delete all entries
                cursor.execute("DELETE FROM optimization_entries")
                
                # Delete all conversations
                cursor.execute("DELETE FROM conversations")
                conn.commit()
        except Exception as e:
            print(f"Error clearing all conversations: {e}")
            raise
