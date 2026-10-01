import sqlite3
import os

db_path = 'alumni.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    
    print("--- USERS TABLE ---")
    users = conn.execute("SELECT id, name, email FROM users").fetchall()
    for u in users:
        print(f"ID: {u['id']}, Name: {u['name']}, Email: {u['email']}")
        
    print("\n--- TEMP_USERS TABLE ---")
    temps = conn.execute("SELECT id, name, email FROM temp_users").fetchall()
    for t in temps:
        print(f"ID: {t['id']}, Name: {t['name']}, Email: {t['email']}")
    
    conn.close()
else:
    print(f"Database {db_path} not found.")
