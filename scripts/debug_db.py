import sqlite3

try:
    conn = sqlite3.connect('college_pro.db')
    cursor = conn.cursor()
    
    print("--- USERS TABLE SCHEMA ---")
    cursor.execute("PRAGMA table_info(users)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
        
    print("\n--- SAMPLE USER ---")
    cursor.execute("SELECT * FROM users LIMIT 1")
    user = cursor.fetchone()
    print(user)
    
    conn.close()
except Exception as e:
    print(f"Error: {e}")
