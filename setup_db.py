import sqlite3
import os

# Ensure database directory exists
os.makedirs('database', exist_ok=True)

conn = sqlite3.connect('database/fleet.db')
cursor = conn.cursor()

# Create tables
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

# 🔥 AWS nodes (SSH-based)
aws_nodes = [
    ('aws-node1', '52.66.248.14', 'aws', 'ubuntu', None, 'online'),
    ('aws-node2', '13.235.70.67', 'aws', 'ubuntu', None, 'online'),
    ('aws-node3', '13.235.69.190', 'aws', 'ubuntu', None, 'online'),
]

# 🔥 Docker nodes (HTTP-based → NO SSH)
docker_nodes = [
    ('node1', 'localhost:9101', 'docker', None, None, 'online'),
    ('node2', 'localhost:9102', 'docker', None, None, 'online'),
    ('node3', 'localhost:9103', 'docker', None, None, 'online'),
]

# Insert AWS nodes
for node in aws_nodes:
    cursor.execute('''
        INSERT OR IGNORE INTO nodes (name, ip, node_type, username, password, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', node)

# Insert Docker nodes
for node in docker_nodes:
    cursor.execute('''
        INSERT OR IGNORE INTO nodes (name, ip, node_type, username, password, status)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', node)

conn.commit()
conn.close()

print("Database setup complete!")
print("Added AWS nodes:")
for node in aws_nodes:
    print(f"  - {node[0]}: {node[1]}")

print("Added Docker nodes:")
for node in docker_nodes:
    print(f"  - {node[0]}: {node[1]}")