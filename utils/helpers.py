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
import io
import base64
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
# File Uploads (Supports Local Disk & Serverless / Vercel Base64 Fallback)
# ─────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    """Check if file extension is in the allowed set."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS


def save_uploaded_file(file, prefix: str = 'photo', user_id: Optional[int] = None, folder: str = UPLOAD_FOLDER, max_dim: int = 400) -> Optional[str]:
    """
    Safely process and save uploaded image.
    Works seamlessly on local development AND serverless platforms (Vercel, AWS Lambda).

    1. If not running on Vercel:
       Attempts to save to local folder and returns the relative web URL.
    2. If running on Vercel OR if filesystem is read-only (OSError Errno 30):
       Reads the image bytes in memory, resizes/optimizes to max_dim x max_dim,
       and returns a Base64 Data URI ('data:image/jpeg;base64,...').
       This persists in the database and renders natively in all <img> tags!
    """
    if not file or not file.filename:
        return None

    if not allowed_file(file.filename):
        return None

    try:
        ext = file.filename.rsplit('.', 1)[1].lower()
        file_bytes = file.read()
        if not file_bytes:
            return None

        # Check if we should attempt local filesystem write
        if not os.environ.get('VERCEL'):
            try:
                os.makedirs(folder, exist_ok=True)
                uid_part = f"_{user_id}" if user_id is not None else ""
                filename = secure_filename(f"{prefix}{uid_part}_{datetime.now().timestamp()}.{ext}")
                filepath = os.path.join(folder, filename)
                with open(filepath, 'wb') as f:
                    f.write(file_bytes)
                web_path = filepath.replace('\\', '/')
                if not web_path.startswith('/'):
                    web_path = '/' + web_path
                return web_path
            except OSError as fs_err:
                logger.warning(f"Local filesystem save failed ({fs_err}). Falling back to Base64 Data URI.")

        # Vercel / Serverless / Read-Only Fallback: Base64 Data URI
        try:
            from PIL import Image
            img = Image.open(io.BytesIO(file_bytes))
            fmt = 'PNG' if ext == 'png' else 'JPEG'
            if fmt == 'JPEG' and img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
            out_buf = io.BytesIO()
            img.save(out_buf, format=fmt, quality=85, optimize=True)
            encoded = base64.b64encode(out_buf.getvalue()).decode('utf-8')
            mime = 'image/png' if fmt == 'PNG' else 'image/jpeg'
            return f"data:{mime};base64,{encoded}"
        except Exception as pil_err:
            logger.debug(f"Pillow resize skipped ({pil_err}), using raw bytes")
            encoded = base64.b64encode(file_bytes).decode('utf-8')
            mime = f"image/{ext}" if ext != 'jpg' else 'image/jpeg'
            return f"data:{mime};base64,{encoded}"

    except Exception as e:
        logger.error(f"save_uploaded_file error: {e}")
        return None


def save_profile_photo(request_files, user_id: int, role: str) -> Optional[str]:
    """
    Handle profile picture upload from request.files.
    """
    if 'profile_pic' not in request_files:
        return None

    file = request_files['profile_pic']
    return save_uploaded_file(file, prefix=role, user_id=user_id, folder=UPLOAD_FOLDER)


def save_company_logo(request_files) -> Optional[str]:
    """
    Handle company logo upload from request.files.
    """
    if 'company_logo' not in request_files:
        return None

    file = request_files['company_logo']
    return save_uploaded_file(file, prefix='logo', folder=COMPANY_LOGOS_FOLDER, max_dim=300)


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
