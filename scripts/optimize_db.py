import sqlite3
import os

def optimize_database():
    db_path = os.path.join('data', 'college_pro.db')
    if not os.path.exists(db_path):
        print(f"Error: Database not found at {db_path}")
        return

    print(f"Optimizing database at {db_path}...")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # 1. Users table optimizations
        print("Creating indexes for 'users' table...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_name ON users(name)")

        # 2. Registration log optimizations
        print("Creating indexes for 'registration_log' table...")
        # Check if table exists first
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='registration_log'")
        if cursor.fetchone():
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reglog_role ON registration_log(role)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_reglog_date ON registration_log(registered_at)")

        # 3. Connections optimizations
        print("Creating indexes for 'connections' table...")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='connections'")
        if cursor.fetchone():
            # Standardizing connection search
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_u1 ON connections(user_id_1)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_connections_u2 ON connections(user_id_2)")

        # 4. Connection requests optimizations
        print("Creating indexes for 'connection_requests' table...")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_connreq_sender ON connection_requests(sender_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_connreq_receiver ON connection_requests(receiver_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_connreq_status ON connection_requests(status)")

        conn.commit()
        print("✅ Database optimization complete! Indexing successful.")

    except Exception as e:
        print(f"❌ Error during optimization: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    optimize_database()
