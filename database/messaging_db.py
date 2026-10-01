"""
Database helper functions for Alumni Hub Messaging System
Handles all CRUD operations for messages, conversations, and system controls
"""

import sqlite3
from datetime import datetime
from contextlib import contextmanager

DB_NAME = 'college_pro.db'


@contextmanager
def get_db_connection():
    """Get database connection with proper configuration"""
    conn = sqlite3.connect(DB_NAME, timeout=20.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ==================== MESSAGING LOCK FUNCTIONS ====================

def get_messaging_lock_status():
    """Get current messaging lock status"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, is_locked, locked_by, locked_at, reason
            FROM messaging_lock
            WHERE id = 1
        ''')
        result = cursor.fetchone()
        if result:
            return {
                'id': result['id'],
                'is_locked': bool(result['is_locked']),
                'locked_by': result['locked_by'],
                'locked_at': result['locked_at'],
                'reason': result['reason']
            }
        return None


def lock_messaging(admin_id, reason=''):
    """Lock public messaging system"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE messaging_lock
            SET is_locked = 1, locked_by = ?, locked_at = ?, reason = ?
            WHERE id = 1
        ''', (admin_id, datetime.utcnow().isoformat(), reason))
        return cursor.rowcount > 0


def unlock_messaging():
    """Unlock public messaging system"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE messaging_lock
            SET is_locked = 0, locked_by = NULL, locked_at = NULL, reason = NULL
            WHERE id = 1
        ''')
        return cursor.rowcount > 0


def is_messaging_locked():
    """Check if messaging is currently locked"""
    status = get_messaging_lock_status()
    return status['is_locked'] if status else False


# ==================== USER SUSPENSION FUNCTIONS ====================

def is_user_suspended(user_id):
    """Check if a specific user is suspended"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT is_suspended FROM users WHERE id = ?', (user_id,))
        result = cursor.fetchone()
        return bool(result['is_suspended']) if result else False


def suspend_user(user_id, admin_id, reason=''):
    """Suspend a user from messaging"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET is_suspended = 1
            WHERE id = ?
        ''', (user_id,))
        # We could also log this in a separate moderation_log table if it existed
        return cursor.rowcount > 0


def unsuspend_user(user_id):
    """Unsuspend a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE users
            SET is_suspended = 0
            WHERE id = ?
        ''', (user_id,))
        return cursor.rowcount > 0


def get_suspended_users():
    """Get list of all suspended users"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, email, role, profile_pic
            FROM users
            WHERE is_suspended = 1
        ''')
        return [dict(row) for row in cursor.fetchall()]


# ==================== PUBLIC MESSAGE FUNCTIONS ====================

def send_public_message(sender_id, content):
    """Send a public message (visible to all)"""
    if is_messaging_locked() or is_user_suspended(sender_id):
        return None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO public_messages (sender_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (sender_id, content, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        return cursor.lastrowid


def get_public_messages(limit=50, offset=0, include_hidden=False):
    """Get public messages with optional pagination"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        where_clause = "WHERE 1=1"
        if not include_hidden:
            where_clause += " AND is_hidden = 0"

        cursor.execute(f'''
            SELECT
                pm.id, pm.sender_id, pm.content, pm.is_hidden,
                pm.created_at, pm.updated_at, pm.deleted_by,
                u.name, u.profile_pic, u.role, u.phone
            FROM public_messages pm
            JOIN users u ON pm.sender_id = u.id
            {where_clause}
            ORDER BY pm.created_at DESC
            LIMIT ? OFFSET ?
        ''', (limit, offset))

        return [dict(row) for row in cursor.fetchall()]


def delete_public_message(message_id, admin_id):
    """Admin delete public message (soft delete - mark as deleted)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE public_messages
            SET deleted_by = ?
            WHERE id = ?
        ''', (admin_id, message_id))
        return cursor.rowcount > 0


def hide_all_public_messages():
    """Hide all public messages (when system is locked)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE public_messages
            SET is_hidden = 1
            WHERE is_hidden = 0 AND deleted_by IS NULL
        ''')
        return cursor.rowcount


def unhide_all_public_messages():
    """Show all public messages (when system is unlocked)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE public_messages
            SET is_hidden = 0
            WHERE is_hidden = 1 AND deleted_by IS NULL
        ''')
        return cursor.rowcount


def get_public_message_count():
    """Get total count of public messages"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) as count FROM public_messages WHERE deleted_by IS NULL')
        result = cursor.fetchone()
        return result['count']


# ==================== PRIVATE MESSAGE FUNCTIONS ====================

def send_private_message(sender_id, receiver_id, content):
    """Send a private message"""
    if is_user_suspended(sender_id):
        return None

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO private_messages (sender_id, receiver_id, content, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (sender_id, receiver_id, content, datetime.utcnow().isoformat(), datetime.utcnow().isoformat()))
        message_id = cursor.lastrowid

        # Update or create conversation
        user_1 = min(sender_id, receiver_id)
        user_2 = max(sender_id, receiver_id)

        cursor.execute('''
            INSERT OR IGNORE INTO conversations (user_id_1, user_id_2, created_at)
            VALUES (?, ?, ?)
        ''', (user_1, user_2, datetime.utcnow().isoformat()))

        # Update last message
        cursor.execute('''
            UPDATE conversations
            SET last_message_id = ?, last_message_at = ?
            WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        ''', (message_id, datetime.utcnow().isoformat(), user_1, user_2, user_2, user_1))

        return message_id


def get_conversation_messages(user_id_1, user_id_2, limit=50, offset=0):
    """Get all messages in a conversation"""
    user_1 = min(user_id_1, user_id_2)
    user_2 = max(user_id_1, user_id_2)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                pm.id, pm.sender_id, pm.receiver_id, pm.content,
                pm.is_read, pm.read_at, pm.created_at, pm.updated_at,
                pm.deleted_by_sender, pm.deleted_by_receiver,
                u.name, u.profile_pic, u.role
            FROM private_messages pm
            JOIN users u ON pm.sender_id = u.id
            WHERE (pm.sender_id = ? AND pm.receiver_id = ?)
               OR (pm.sender_id = ? AND pm.receiver_id = ?)
            AND pm.deleted_by_sender = 0 AND pm.deleted_by_receiver = 0
            ORDER BY pm.created_at ASC
            LIMIT ? OFFSET ?
        ''', (user_1, user_2, user_2, user_1, limit, offset))

        return [dict(row) for row in cursor.fetchall()]


def get_user_conversations(user_id):
    """Get all conversations for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT
                c.id, c.user_id_1, c.user_id_2, c.last_message_id, c.last_message_at,
                CASE
                    WHEN c.user_id_1 = ? THEN u2.id
                    ELSE u1.id
                END as other_user_id,
                CASE
                    WHEN c.user_id_1 = ? THEN u2.name
                    ELSE u1.name
                END as other_user_name,
                CASE
                    WHEN c.user_id_1 = ? THEN u2.profile_pic
                    ELSE u1.profile_pic
                END as other_user_pic,
                CASE
                    WHEN c.user_id_1 = ? THEN u2.role
                    ELSE u1.role
                END as other_user_role,
                CASE
                    WHEN c.user_id_1 = ? THEN u2.phone
                    ELSE u1.phone
                END as other_user_phone,
                pm.content as last_message_content,
                (SELECT COUNT(*) FROM private_messages
                 WHERE receiver_id = ?
                 AND is_read = 0
                 AND (sender_id = CASE WHEN c.user_id_1 = ? THEN c.user_id_2 ELSE c.user_id_1 END)
                ) as unread_count
            FROM conversations c
            LEFT JOIN users u1 ON c.user_id_1 = u1.id
            LEFT JOIN users u2 ON c.user_id_2 = u2.id
            LEFT JOIN private_messages pm ON c.last_message_id = pm.id
            WHERE c.user_id_1 = ? OR c.user_id_2 = ?
            ORDER BY c.last_message_at DESC
        ''', (user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id, user_id))

        return [dict(row) for row in cursor.fetchall()]


def mark_message_as_read(message_id, reader_id):
    """Mark a private message as read"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE private_messages
            SET is_read = 1, read_at = ?
            WHERE id = ? AND receiver_id = ?
        ''', (datetime.utcnow().isoformat(), message_id, reader_id))
        return cursor.rowcount > 0


def mark_conversation_as_read(user_id_1, user_id_2, reader_id):
    """Mark all unread messages in a conversation as read"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE private_messages
            SET is_read = 1, read_at = ?
            WHERE receiver_id = ?
            AND is_read = 0
            AND ((sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?))
        ''', (datetime.utcnow().isoformat(), reader_id, user_id_1, reader_id, user_id_2, reader_id))
        return cursor.rowcount


def delete_private_message(message_id, user_id):
    """Delete a private message (soft delete - only for user's view)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Check if user is sender or receiver
        cursor.execute('SELECT sender_id, receiver_id FROM private_messages WHERE id = ?', (message_id,))
        result = cursor.fetchone()

        if not result:
            return False

        if result['sender_id'] == user_id:
            cursor.execute('''
                UPDATE private_messages
                SET deleted_by_sender = 1
                WHERE id = ?
            ''', (message_id,))
        elif result['receiver_id'] == user_id:
            cursor.execute('''
                UPDATE private_messages
                SET deleted_by_receiver = 1
                WHERE id = ?
            ''', (message_id,))
        else:
            return False

        return cursor.rowcount > 0


def get_unread_message_count(user_id):
    """Get count of unread private messages for a user"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*) as count FROM private_messages
            WHERE receiver_id = ? AND is_read = 0
        ''', (user_id,))
        result = cursor.fetchone()
        return result['count']


# ==================== MESSAGE SEARCH FUNCTIONS ====================

def search_messages(query, user_id=None, message_type='all', limit=20):
    """Search messages by content"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        if message_type == 'public':
            sql = '''
                SELECT
                    'public' as type,
                    pm.id, pm.sender_id, pm.content, pm.created_at,
                    u.name, u.profile_pic, u.role
                FROM public_messages pm
                JOIN users u ON pm.sender_id = u.id
                WHERE (pm.content LIKE ? OR u.name LIKE ?)
                AND pm.is_hidden = 0 AND pm.deleted_by IS NULL
                ORDER BY pm.created_at DESC
                LIMIT ?
            '''
            search_term = f"%{query}%"
            cursor.execute(sql, (search_term, search_term, limit))

        elif message_type == 'private':
            sql = '''
                SELECT
                    'private' as type,
                    pm.id, pm.sender_id, pm.receiver_id, pm.content, pm.created_at,
                    u.name, u.profile_pic, u.role
                FROM private_messages pm
                JOIN users u ON pm.sender_id = u.id
                WHERE ((pm.sender_id = ? OR pm.receiver_id = ?)
                       AND (pm.content LIKE ? OR u.name LIKE ?))
                AND pm.deleted_by_sender = 0 AND pm.deleted_by_receiver = 0
                ORDER BY pm.created_at DESC
                LIMIT ?
            '''
            search_term = f"%{query}%"
            cursor.execute(sql, (user_id, user_id, search_term, search_term, limit))

        else:  # all
            # Combined search
            results = []

            # Search public messages
            sql_public = '''
                SELECT
                    'public' as type,
                    pm.id, pm.sender_id, pm.content, pm.created_at,
                    u.name, u.profile_pic, u.role
                FROM public_messages pm
                JOIN users u ON pm.sender_id = u.id
                WHERE (pm.content LIKE ? OR u.name LIKE ?)
                AND pm.is_hidden = 0 AND pm.deleted_by IS NULL
                ORDER BY pm.created_at DESC
                LIMIT ?
            '''
            search_term = f"%{query}%"
            cursor.execute(sql_public, (search_term, search_term, limit // 2))
            results.extend([dict(row) for row in cursor.fetchall()])

            # Search private messages
            if user_id:
                sql_private = '''
                    SELECT
                        'private' as type,
                        pm.id, pm.sender_id, pm.receiver_id, pm.content, pm.created_at,
                        u.name, u.profile_pic, u.role
                    FROM private_messages pm
                    JOIN users u ON pm.sender_id = u.id
                    WHERE ((pm.sender_id = ? OR pm.receiver_id = ?)
                           AND (pm.content LIKE ? OR u.name LIKE ?))
                    AND pm.deleted_by_sender = 0 AND pm.deleted_by_receiver = 0
                    ORDER BY pm.created_at DESC
                    LIMIT ?
                '''
                cursor.execute(sql_private, (user_id, user_id, search_term, search_term, limit // 2))
                results.extend([dict(row) for row in cursor.fetchall()])

            return results[:limit]

        return [dict(row) for row in cursor.fetchall()]


# ==================== CONVERSATION MANAGEMENT ====================

def get_conversation_id(user_id_1, user_id_2):
    """Get conversation ID for two users"""
    user_1 = min(user_id_1, user_id_2)
    user_2 = max(user_id_1, user_id_2)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id FROM conversations
            WHERE user_id_1 = ? AND user_id_2 = ?
        ''', (user_1, user_2))
        result = cursor.fetchone()
        return result['id'] if result else None


def create_conversation(user_id_1, user_id_2):
    """Create a new conversation between two users"""
    user_1 = min(user_id_1, user_id_2)
    user_2 = max(user_id_1, user_id_2)

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR IGNORE INTO conversations (user_id_1, user_id_2, created_at)
            VALUES (?, ?, ?)
        ''', (user_1, user_2, datetime.utcnow().isoformat()))
        return cursor.lastrowid


# ==================== STATISTICS ====================

def get_messaging_statistics():
    """Get messaging system statistics"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM public_messages WHERE deleted_by IS NULL')
        public_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM private_messages')
        private_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM conversations')
        conversation_count = cursor.fetchone()['count']

        status = get_messaging_lock_status()

        return {
            'total_public_messages': public_count,
            'total_private_messages': private_count,
            'total_conversations': conversation_count,
            'system_locked': status['is_locked'] if status else False,
            'locked_at': status['locked_at'] if status else None,
            'locked_by': status['locked_by'] if status else None
        }
