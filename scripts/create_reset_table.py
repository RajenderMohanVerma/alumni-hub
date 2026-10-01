import sqlite3
from app import DB_NAME

def create_table():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    
    # Create password_resets table
    c.execute('''
        CREATE TABLE IF NOT EXISTS password_resets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            otp TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ password_resets table created successfully.")

if __name__ == "__main__":
    create_table()
