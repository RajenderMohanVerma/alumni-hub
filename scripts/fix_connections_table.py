import sqlite3

# Connect to database
conn = sqlite3.connect('college_pro.db')
c = conn.cursor()

# Check if connections table exists and has correct schema
try:
    result = c.execute("PRAGMA table_info(connections)").fetchall()
    print("Current connections table schema:")
    for row in result:
        print(row)
    
    # Check if user_id_1 and user_id_2 exist
    columns = [row[1] for row in result]
    if 'user_id_1' not in columns or 'user_id_2' not in columns:
        print("\nMissing required columns! Recreating table...")
        
        # Drop and recreate
        c.execute("DROP TABLE IF EXISTS connections")
        c.execute('''
            CREATE TABLE connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id_1 INTEGER NOT NULL,
                user_id_2 INTEGER NOT NULL,
                connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id_1) REFERENCES users(id),
                FOREIGN KEY (user_id_2) REFERENCES users(id),
                UNIQUE(user_id_1, user_id_2)
            )
        ''')
        conn.commit()
        print("Connections table recreated successfully!")
    else:
        print("\nConnections table schema is correct!")
        
except Exception as e:
    print(f"Error: {e}")
    
conn.close()
