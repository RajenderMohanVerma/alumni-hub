import sqlite3
from flask import current_app

def get_db_connection():
    """
    Get a database connection using current_app config.
    Using current_app prevents circular imports with app.py.
    """
    db_name = current_app.config.get('DB_NAME', 'data/alumni.db')
    conn = sqlite3.connect(db_name, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn
