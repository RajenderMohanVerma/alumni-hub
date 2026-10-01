import sqlite3
from app import app
from db_utils import get_db_connection


def migrate_connection_monitoring():
    """Add schema updates required for admin connection monitoring."""
    with app.app_context():
        conn = get_db_connection()
        cur = conn.cursor()

        print("Running connection monitoring migration...")

        # Ensure accepted_at exists in connection_requests
        try:
            cur.execute("ALTER TABLE connection_requests ADD COLUMN accepted_at TIMESTAMP")
            print("Added column: connection_requests.accepted_at")
        except sqlite3.OperationalError:
            print("Column already exists: connection_requests.accepted_at")

        # Ensure updated_at exists in connection_requests
        try:
            cur.execute("ALTER TABLE connection_requests ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Added column: connection_requests.updated_at")
        except sqlite3.OperationalError:
            print("Column already exists: connection_requests.updated_at")

        # Ensure user_activity table exists
        cur.execute(
            '''
            CREATE TABLE IF NOT EXISTS user_activity (
                user_id INTEGER PRIMARY KEY,
                last_login TIMESTAMP,
                online_status TEXT DEFAULT 'offline',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            '''
        )
        print("Ensured table: user_activity")

        # Backfill activity rows for existing users
        cur.execute(
            '''
            INSERT OR IGNORE INTO user_activity (user_id, online_status)
            SELECT id, 'offline' FROM users
            '''
        )
        print("Backfilled user_activity rows for existing users")

        cur.execute("CREATE INDEX IF NOT EXISTS idx_connection_requests_created_at ON connection_requests(created_at)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_connection_requests_status ON connection_requests(status)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_user_activity_last_login ON user_activity(last_login)")
        print("Ensured monitoring indexes")

        conn.commit()
        conn.close()
        print("Connection monitoring migration completed.")


if __name__ == "__main__":
    migrate_connection_monitoring()
