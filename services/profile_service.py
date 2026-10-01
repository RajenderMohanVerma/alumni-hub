"""
services/profile_service.py
============================
Business logic for user profile operations.
Extracted from app.py to keep routes thin and logic reusable.

Functions:
    update_user_profile()   — Update user's basic profile fields + photo
    ensure_faculty_profile() — Create a default faculty profile if missing
    get_user_stats()         — Get dashboard stats for a user role
"""

import logging
from db_utils import get_db_connection
from utils.helpers import save_profile_photo

logger = logging.getLogger(__name__)


def update_user_profile(user_id: int, role: str, form_data: dict, request_files=None) -> bool:
    """
    Update a user's profile (name, phone, profile_pic, role-specific fields).

    Args:
        user_id: The user's database ID.
        role: The user's role (student, alumni, faculty, admin).
        form_data: Dict of form field values.
        request_files: Flask request.files for photo upload.

    Returns:
        True on success, False on failure.
    """
    conn = None
    try:
        conn = get_db_connection()

        # Handle profile picture upload
        profile_pic = None
        if request_files:
            profile_pic = save_profile_photo(request_files, user_id, role)

        # Update users table (common fields)
        name = form_data.get('name', '').strip()
        phone = form_data.get('phone', '').strip()

        if profile_pic:
            conn.execute(
                'UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE id = ?',
                (name, phone, profile_pic, user_id)
            )
        else:
            conn.execute(
                'UPDATE users SET name = ?, phone = ? WHERE id = ?',
                (name, phone, user_id)
            )

        conn.commit()
        return True

    except Exception as e:
        logger.error(f"Profile update failed for user {user_id}: {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if conn:
            conn.close()


def ensure_faculty_profile(conn, user_id: int) -> None:
    """
    Create a default faculty_profile row if one doesn't exist.
    Called when a faculty member first accesses their dashboard.
    """
    existing = conn.execute(
        'SELECT id FROM faculty_profile WHERE user_id = ?', (user_id,)
    ).fetchone()

    if not existing:
        try:
            conn.execute('''
                INSERT INTO faculty_profile (user_id, employee_id, department, designation)
                VALUES (?, ?, ?, ?)
            ''', (user_id, f'TEMP_{user_id}', 'Not Set', 'Not Set'))
            conn.commit()
            logger.info(f"Created default faculty profile for user {user_id}")
        except Exception as e:
            logger.warning(f"Faculty profile creation skipped (may already exist): {e}")
