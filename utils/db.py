"""
utils/db.py
============
Database utility functions and context manager.

Provides a safe context manager for database connections
that guarantees cleanup even on exceptions.

Usage:
    from utils.db import get_db, query_one, query_all

    # Context manager (auto-close + rollback on error):
    with get_db() as conn:
        conn.execute('INSERT INTO ...', (...))
        conn.commit()

    # Quick helpers:
    user = query_one('SELECT * FROM users WHERE id = ?', (user_id,))
    users = query_all('SELECT * FROM users WHERE role = ?', ('student',))
"""

import sqlite3
import logging
from contextlib import contextmanager
from flask import current_app

logger = logging.getLogger(__name__)


@contextmanager
def get_db():
    """
    Context manager for database connections.
    Automatically closes the connection and rolls back on exception.

    Usage:
        with get_db() as conn:
            conn.execute(...)
            conn.commit()
    """
    conn = None
    try:
        db_name = current_app.config.get('DB_NAME', 'data/college_pro.db')
        conn = sqlite3.connect(db_name, timeout=20.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        yield conn
    except Exception:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def query_one(sql: str, params: tuple = ()) -> sqlite3.Row:
    """Execute a query and return a single row or None."""
    with get_db() as conn:
        return conn.execute(sql, params).fetchone()


def query_all(sql: str, params: tuple = ()) -> list:
    """Execute a query and return all rows."""
    with get_db() as conn:
        return conn.execute(sql, params).fetchall()


def execute_sql(sql: str, params: tuple = (), commit: bool = True) -> int:
    """
    Execute a write query (INSERT/UPDATE/DELETE).
    Returns the lastrowid for INSERTs.
    """
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        if commit:
            conn.commit()
        return cursor.lastrowid
