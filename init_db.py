import sqlite3
import os
from config import Config

def init_database():
    
    # Ensure database directory exists
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    # Create nodes table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nodes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            ip TEXT NOT NULL UNIQUE,
            node_type TEXT DEFAULT 'custom',
            username TEXT,
            key_path TEXT,
            password TEXT,
            status TEXT DEFAULT 'pending',
            onboarded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            last_reboot TIMESTAMP
        )
    ''')
    
    # Create audit_log table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            node_id INTEGER,
            action TEXT,
            status TEXT,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (node_id) REFERENCES nodes(id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print(f"Database initialized at {Config.DATABASE_PATH}")

if __name__ == '__main__':
    init_database()
