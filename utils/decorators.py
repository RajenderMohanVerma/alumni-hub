"""
utils/decorators.py
====================
Reusable Flask decorators for role-based access control.

Usage:
    from utils.decorators import role_required

    @app.route('/admin/dashboard')
    @login_required
    @role_required('admin')
    def admin_dashboard():
        ...

    # Multiple roles:
    @role_required('admin', 'faculty')
    def some_route():
        ...
"""

from functools import wraps
from flask import redirect, url_for, flash, jsonify, request
from flask_login import current_user


def role_required(*roles):
    """
    Decorator that restricts access to users with specific roles.

    Args:
        *roles: One or more role strings (e.g., 'admin', 'student', 'alumni', 'faculty').

    Returns:
        - HTML routes: redirect to home with flash message.
        - API routes (Accept: application/json or /api/): return JSON 403.
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('login'))

            if current_user.role not in roles:
                # Check if this is an API request
                is_api = (
                    request.path.startswith('/api/') or
                    request.accept_mimetypes.best == 'application/json'
                )
                if is_api:
                    return jsonify({'success': False, 'error': 'Unauthorized'}), 403

                flash('Access denied! You do not have permission to view this page.', 'danger')
                return redirect(url_for('home'))

            return f(*args, **kwargs)
        return decorated_function
    return decorator
