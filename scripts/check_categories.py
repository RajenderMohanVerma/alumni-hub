import sqlite3
import os

db_path = 'data/college_pro.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT id, title, category FROM jobs LIMIT 10")
    rows = cursor.fetchall()
    print("--- data/college_pro.db ---")
    for row in rows:
        print(f"ID: {row['id']}, Title: {row['title']}, Category: '{row['category']}'")
    conn.close()
else:
    print("data/college_pro.db not found")
