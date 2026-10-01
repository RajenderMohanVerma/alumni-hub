"""
utils/helpers.py
=================
Reusable helper functions extracted from app.py to eliminate
duplicate code and improve maintainability.

Functions:
    generate_otp()          — Generate a numeric OTP
    save_profile_photo()    — Handle profile picture upload
    save_company_logo()     — Handle company logo upload
    normalize_phone()       — Clean phone number formatting
    parse_db_timestamp()    — Safely parse SQLite timestamps
    safe_error_message()    — Sanitize error messages for users
    extract_job_form_data() — Extract job form fields from request
"""

import os
import secrets
import string
import logging
from datetime import datetime
from typing import Optional, Tuple
from werkzeug.utils import secure_filename
from markupsafe import escape

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
MAX_UPLOAD_SIZE_MB = 16
PASSWORD_MIN_LENGTH = 8   # Single source of truth
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 600  # 10 minutes

UPLOAD_FOLDER = 'static/uploads'
COMPANY_LOGOS_FOLDER = 'static/uploads/company_logos'


# ─────────────────────────────────────────────
# OTP
# ─────────────────────────────────────────────
def generate_otp(length: int = OTP_LENGTH) -> str:
    """Generate a cryptographically secure numeric OTP."""
    return ''.join(secrets.choice(string.digits) for _ in range(length))


# ─────────────────────────────────────────────
# File Uploads
# ─────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    """Check if file extension is in the allowed set."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_profile_photo(request_files, user_id: int, role: str) -> Optional[str]:
    """
    Handle profile picture upload from request.files.

    Args:
        request_files: Flask request.files object
        user_id: User's database ID
        role: User role (student, alumni, etc.)

    Returns:
        URL path string (e.g., '/static/uploads/student_1_....jpg') or None
    """
    if 'profile_pic' not in request_files:
        return None

    file = request_files['profile_pic']
    if not file or not file.filename or not allowed_file(file.filename):
        return None

    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"{role}_{user_id}_{datetime.now().timestamp()}.{ext}")
        filepath = os.path.join(UPLOAD_FOLDER, filename)

        # Ensure directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(filepath)

        return f"/static/uploads/{filename}"
    except Exception as e:
        logger.error(f"Profile photo upload failed: {e}")
        return None


def save_company_logo(request_files) -> Optional[str]:
    """
    Handle company logo upload from request.files.

    Returns:
        URL path string or None.
    """
    if 'company_logo' not in request_files:
        return None

    file = request_files['company_logo']
    if not file or not file.filename or not allowed_file(file.filename):
        return None

    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        filename = secure_filename(f"logo_{datetime.now().timestamp()}.{ext}")
        filepath = os.path.join(COMPANY_LOGOS_FOLDER, filename)

        os.makedirs(COMPANY_LOGOS_FOLDER, exist_ok=True)
        file.save(filepath)

        return f"/static/uploads/company_logos/{filename}"
    except Exception as e:
        logger.error(f"Company logo upload failed: {e}")
        return None


# ─────────────────────────────────────────────
# Phone Number
# ─────────────────────────────────────────────
def normalize_phone(phone: str) -> str:
    """
    Clean and normalize a phone number string.
    Removes non-digit chars except leading +.
    Ensures +91 prefix for Indian numbers.
    """
    if not phone:
        return ''

    phone = phone.strip()

    # Keep leading + if present
    if phone.startswith('+'):
        cleaned = '+' + ''.join(c for c in phone[1:] if c.isdigit())
    else:
        cleaned = ''.join(c for c in phone if c.isdigit())

    # Add +91 if 10-digit Indian number
    if len(cleaned) == 10 and cleaned.isdigit():
        cleaned = '+91' + cleaned

    return cleaned


# ─────────────────────────────────────────────
# Timestamp Parsing
# ─────────────────────────────────────────────
def parse_db_timestamp(timestamp_str: str) -> Optional[datetime]:
    """
    Safely parse a SQLite CURRENT_TIMESTAMP value.
    Handles multiple formats: with/without fractional seconds, T separator.
    """
    if not timestamp_str:
        return None

    formats = [
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%d %H:%M:%S.%f',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp_str, fmt)
        except ValueError:
            continue

    logger.warning(f"Could not parse timestamp: {timestamp_str}")
    return None


# ─────────────────────────────────────────────
# Error Sanitization
# ─────────────────────────────────────────────
def safe_error_message(error: Exception, default: str = "An unexpected error occurred.") -> str:
    """
    Return a user-safe error message. Never expose internal details.
    Logs the full error for debugging.
    """
    logger.error(f"Internal error: {error}", exc_info=True)
    return default


# ─────────────────────────────────────────────
# HTML Sanitization
# ─────────────────────────────────────────────
def sanitize_html(text: str) -> str:
    """Escape HTML special characters to prevent XSS/injection."""
    if not text:
        return ''
    return str(escape(text))


# ─────────────────────────────────────────────
# Password Validation
# ─────────────────────────────────────────────
def validate_password(password: str) -> Tuple[bool, str]:
    """
    Validate password strength. Returns (is_valid, message).
    Consistent across registration, reset, and change flows.
    """
    if not password:
        return False, "Password is required."
    if len(password) < PASSWORD_MIN_LENGTH:
        return False, f"Password must be at least {PASSWORD_MIN_LENGTH} characters long."
    return True, "Password is valid."


# ─────────────────────────────────────────────
# Job Form Extraction
# ─────────────────────────────────────────────
def extract_job_form_data(form) -> dict:
    """
    Extract all job form fields from a Flask request.form object.
    Centralizes the 30+ field extraction to avoid duplication.

    Args:
        form: Flask request.form (ImmutableMultiDict)

    Returns:
        dict with all job-related fields.
    """
    fields = [
        'title', 'company', 'location', 'salary', 'job_type',
        'apply_link', 'description', 'required_skills', 'category',
        'work_mode', 'employment_type', 'eligible_branch',
        'eligible_batch', 'qualification', 'min_cgpa',
        'experience_required', 'skills_preferred', 'perks',
        'selection_process', 'joining_date', 'target_role',
        'skill_level', 'apply_method', 'company_website',
        'salary_perks', 'ctc_range', 'company_name',
        'skills_required', 'deadline'
    ]

    data = {}
    for field in fields:
        data[field] = form.get(field, '').strip()

    # Integer fields
    data['openings'] = form.get('openings', type=int, default=0)

    return data
