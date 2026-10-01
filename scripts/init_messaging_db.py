"""
Database migration script for Alumni Hub Messaging System
Creates all necessary tables for public messaging, private messaging, and admin controls
"""

import sqlite3
from datetime import datetime
import os

DB_NAME = os.path.join('data', 'college_pro.db')


def init_messaging_db():
    """Initialize all messaging-related database tables"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("Creating messaging database tables...")

    # Create messaging_lock table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS messaging_lock (
            id INTEGER PRIMARY KEY,
            is_locked BOOLEAN DEFAULT 0,
            locked_by INTEGER,
            locked_at TIMESTAMP,
            reason TEXT,
            FOREIGN KEY(locked_by) REFERENCES users(id)
        )
    ''')
    print("✓ Created messaging_lock table")

    # Create public_messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS public_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_hidden BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_by INTEGER,
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(deleted_by) REFERENCES users(id)
        )
    ''')
    print("✓ Created public_messages table")

    # Create private_messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS private_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            read_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            deleted_by_sender BOOLEAN DEFAULT 0,
            deleted_by_receiver BOOLEAN DEFAULT 0,
            FOREIGN KEY(sender_id) REFERENCES users(id),
            FOREIGN KEY(receiver_id) REFERENCES users(id)
        )
    ''')
    print("✓ Created private_messages table")

    # Create conversations table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id_1 INTEGER NOT NULL,
            user_id_2 INTEGER NOT NULL,
            last_message_id INTEGER,
            last_message_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id_1) REFERENCES users(id),
            FOREIGN KEY(user_id_2) REFERENCES users(id),
            FOREIGN KEY(last_message_id) REFERENCES private_messages(id),
            UNIQUE(user_id_1, user_id_2)
        )
    ''')
    print("✓ Created conversations table")

    # Create message_search_index table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_search_index (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id INTEGER NOT NULL,
            message_type TEXT,
            content_index TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    print("✓ Created message_search_index table")

    # Initialize messaging lock (unlocked by default)
    cursor.execute('''
        INSERT OR IGNORE INTO messaging_lock (id, is_locked)
        VALUES (1, 0)
    ''')
    print("✓ Initialized messaging lock state (unlocked by default)")

    conn.commit()
    conn.close()
    print("\n✅ Messaging database tables created successfully!")
    print(f"Database: {DB_NAME}")


if __name__ == '__main__':
    if os.path.exists(DB_NAME):
        print(f"Database {DB_NAME} found. Initializing tables...\n")
        init_messaging_db()
    else:
        print(f"Error: Database {DB_NAME} not found!")
        print(f"Please ensure the database exists at: {os.path.abspath(DB_NAME)}")
