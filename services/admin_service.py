"""
services/admin_service.py
==========================
Business logic for admin dashboard operations.
Consolidates repeated COUNT queries into single efficient queries.

Functions:
    get_role_counts()        — Single query for all role counts
    get_yearly_stats()       — Yearly registration chart data in one query
    get_admin_job_stats()    — Job statistics in one query
"""

import logging
from datetime import datetime
from db_utils import get_db_connection

logger = logging.getLogger(__name__)


def get_user_statistics(conn, user_id: int) -> dict:
    """
    Return social statistics for a user.

    The current platform has a bidirectional connections model and no separate
    followers table. For monitoring consistency, followers/following/connection
    counts are derived from accepted connections.
    """
    row = conn.execute(
        """
        SELECT COUNT(*) AS connection_count
        FROM connections
        WHERE user_id_1 = ? OR user_id_2 = ?
        """,
        (user_id, user_id),
    ).fetchone()

    total = row["connection_count"] if row else 0
    return {
        "total_connections": total,
        "total_followers": total,
        "total_following": total,
    }


def get_all_connections(conn, role_filter: str = "all", search: str = "") -> list:
    """
    Fetch connection request records with sender/receiver profile details.

    Args:
        conn: SQLite connection
        role_filter: 'all', 'student', or 'alumni'
        search: partial name/email text for sender/receiver
    """
    role_filter = (role_filter or "all").strip().lower()
    search = (search or "").strip()
    like_term = f"%{search}%"

    query = """
        SELECT
            cr.id,
            cr.sender_id,
            cr.receiver_id,
            cr.status,
            cr.created_at AS request_sent_at,
            cr.accepted_at AS request_accepted_at,

            su.name AS sender_name,
            su.email AS sender_email,
            su.role AS sender_role,
            COALESCE(sp_sender.department, ap_sender.department, fp_sender.department, su.branch, 'N/A') AS sender_department,
            COALESCE(sp_sender.skills, su.skills, '') AS sender_skills,
            su.current_domain AS sender_current_domain,
            COALESCE(sp_sender.semester, ap_sender.pass_year, su.passing_year) AS sender_passing_year,
            COALESCE(ap_sender.company_name, su.company, '') AS sender_company,

            ru.name AS receiver_name,
            ru.email AS receiver_email,
            ru.role AS receiver_role,
            COALESCE(sp_receiver.department, ap_receiver.department, fp_receiver.department, ru.branch, 'N/A') AS receiver_department,
            COALESCE(sp_receiver.skills, ru.skills, '') AS receiver_skills,
            ru.current_domain AS receiver_current_domain,
            COALESCE(sp_receiver.semester, ap_receiver.pass_year, ru.passing_year) AS receiver_passing_year,
            COALESCE(ap_receiver.company_name, ru.company, '') AS receiver_company
        FROM connection_requests cr
        JOIN users su ON su.id = cr.sender_id
        JOIN users ru ON ru.id = cr.receiver_id

        LEFT JOIN student_profile sp_sender ON sp_sender.user_id = su.id AND su.role = 'student'
        LEFT JOIN alumni_profile ap_sender ON ap_sender.user_id = su.id AND su.role = 'alumni'
        LEFT JOIN faculty_profile fp_sender ON fp_sender.user_id = su.id AND su.role = 'faculty'

        LEFT JOIN student_profile sp_receiver ON sp_receiver.user_id = ru.id AND ru.role = 'student'
        LEFT JOIN alumni_profile ap_receiver ON ap_receiver.user_id = ru.id AND ru.role = 'alumni'
        LEFT JOIN faculty_profile fp_receiver ON fp_receiver.user_id = ru.id AND ru.role = 'faculty'
        WHERE
            (? = 'all' OR su.role = ? OR ru.role = ?)
            AND (
                ? = ''
                OR su.name LIKE ?
                OR su.email LIKE ?
                OR ru.name LIKE ?
                OR ru.email LIKE ?
            )
        ORDER BY cr.created_at DESC
    """

    rows = conn.execute(
        query,
        (
            role_filter,
            role_filter,
            role_filter,
            search,
            like_term,
            like_term,
            like_term,
            like_term,
        ),
    ).fetchall()

    return [dict(r) for r in rows]


def get_connection_activity(conn, role_filter: str = "all", search: str = "") -> list:
    """
    Enrich connection records with social stats, activity status, and
    message counts exchanged between each sender/receiver pair.
    """
    records = get_all_connections(conn, role_filter=role_filter, search=search)
    if not records:
        return []

    result = []
    for row in records:
        sender_id = row["sender_id"]
        receiver_id = row["receiver_id"]

        sender_stats = get_user_statistics(conn, sender_id)
        receiver_stats = get_user_statistics(conn, receiver_id)

        sender_activity = conn.execute(
            """
            SELECT last_login, online_status
            FROM user_activity
            WHERE user_id = ?
            """,
            (sender_id,),
        ).fetchone()

        receiver_activity = conn.execute(
            """
            SELECT last_login, online_status
            FROM user_activity
            WHERE user_id = ?
            """,
            (receiver_id,),
        ).fetchone()

        try:
            msg_row = conn.execute(
                """
                SELECT COUNT(*) AS message_count
                FROM private_messages
                WHERE (sender_id = ? AND receiver_id = ?)
                   OR (sender_id = ? AND receiver_id = ?)
                """,
                (sender_id, receiver_id, receiver_id, sender_id),
            ).fetchone()
            messages_exchanged = msg_row["message_count"] if msg_row else 0
        except Exception:
            # private_messages may not exist in some local setups.
            messages_exchanged = 0

        row["sender_stats"] = sender_stats
        row["receiver_stats"] = receiver_stats
        row["sender_activity"] = {
            "last_login": sender_activity["last_login"] if sender_activity else None,
            "online_status": sender_activity["online_status"] if sender_activity else "offline",
        }
        row["receiver_activity"] = {
            "last_login": receiver_activity["last_login"] if receiver_activity else None,
            "online_status": receiver_activity["online_status"] if receiver_activity else "offline",
        }
        row["messages_exchanged"] = messages_exchanged
        result.append(row)

    return result


def get_role_counts(conn) -> dict:
    """
    Get user counts per role in a SINGLE query instead of 3-4 separate ones.

    Returns:
        {'student': int, 'alumni': int, 'faculty': int, 'admin': int, 'total': int}
    """
    rows = conn.execute(
        "SELECT role, COUNT(*) as cnt FROM users GROUP BY role"
    ).fetchall()

    counts = {'student': 0, 'alumni': 0, 'faculty': 0, 'admin': 0, 'total': 0}
    for row in rows:
        role = row['role']
        cnt = row['cnt']
        if role in counts:
            counts[role] = cnt
        counts['total'] += cnt

    return counts


def get_yearly_stats(conn, num_years: int = 5) -> dict:
    """
    Get yearly registration data for charts in ONE query with GROUP BY,
    instead of 20 separate COUNT queries (4 roles × 5 years).

    Returns:
        {
            'years': ['2022', '2023', ...],
            'students': [10, 15, ...],
            'alumni': [5, 8, ...],
            'faculty': [2, 3, ...],
            'events': [1, 2, ...]
        }
    """
    current_year = datetime.now().year
    years = [str(y) for y in range(current_year - num_years + 1, current_year + 1)]

    # Single query: group by year and role
    rows = conn.execute("""
        SELECT strftime('%Y', created_at) as reg_year, role, COUNT(*) as cnt
        FROM users
        WHERE strftime('%Y', created_at) >= ?
        GROUP BY reg_year, role
    """, (years[0],)).fetchall()

    # Build year→role→count map
    year_map = {y: {'student': 0, 'alumni': 0, 'faculty': 0} for y in years}
    for row in rows:
        yr = row['reg_year']
        role = row['role']
        if yr in year_map and role in year_map[yr]:
            year_map[yr][role] = row['cnt']

    # Events (alumni_meet_registration) separately but also grouped
    event_rows = conn.execute("""
        SELECT strftime('%Y', created_at) as reg_year, COUNT(*) as cnt
        FROM alumni_meet_registration
        WHERE strftime('%Y', created_at) >= ?
        GROUP BY reg_year
    """, (years[0],)).fetchall()

    event_map = {y: 0 for y in years}
    for row in event_rows:
        yr = row['reg_year']
        if yr in event_map:
            event_map[yr] = row['cnt']

    return {
        'years': years,
        'students': [year_map[y]['student'] for y in years],
        'alumni': [year_map[y]['alumni'] for y in years],
        'faculty': [year_map[y]['faculty'] for y in years],
        'events': [event_map[y] for y in years],
    }


def get_admin_job_stats(conn) -> dict:
    """
    Get job statistics in a single query instead of 4 separate ones.

    Returns:
        {'total': int, 'active': int, 'closed': int, 'applications': int}
    """
    stats = {'total': 0, 'active': 0, 'closed': 0, 'applications': 0}

    row = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN is_active = 1 THEN 1 ELSE 0 END) as active,
            SUM(CASE WHEN is_active = 0 THEN 1 ELSE 0 END) as closed
        FROM jobs
    """).fetchone()

    if row:
        stats['total'] = row['total'] or 0
        stats['active'] = row['active'] or 0
        stats['closed'] = row['closed'] or 0

    app_row = conn.execute("SELECT COUNT(*) as cnt FROM job_applications").fetchone()
    stats['applications'] = app_row['cnt'] if app_row else 0

    return stats
