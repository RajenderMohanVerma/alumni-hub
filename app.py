

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, send_from_directory
from flask_socketio import SocketIO
import random
import secrets
import string
import logging
import traceback
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import sqlite3
import os
from config import config
import time
import base64
from extensions import mail
from db_utils import get_db_connection, is_turso, dump_to_sql
from datetime import datetime, timedelta
from dotenv import load_dotenv
from models.recommendation import get_recommended_users, get_recommended_jobs
from flask_apscheduler import APScheduler
from urllib.parse import quote
from utils.decorators import role_required
from utils.helpers import (
    generate_otp, save_profile_photo, save_company_logo,
    normalize_phone, parse_db_timestamp, safe_error_message,
    sanitize_html, validate_password, extract_job_form_data,
    PASSWORD_MIN_LENGTH, OTP_EXPIRY_SECONDS
)
from services.admin_service import get_all_connections, get_connection_activity, get_user_statistics

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger(__name__)


# Load environment variables
load_dotenv()

app = Flask(__name__)
env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.getenv('MAIL_PORT', 587))
app.config['MAIL_USE_TLS'] = os.getenv('MAIL_USE_TLS', 'True') == 'True'
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME', 'alumnihub26@gmail.com')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD', 'jxrp rghf qcow xfne')
# Set sender name as "Alumni Hub" with email
app.config['MAIL_DEFAULT_SENDER'] = ('ALUMNI HUB', os.getenv('MAIL_USERNAME', 'alumnihub26@gmail.com'))

# Initialize SocketIO for real-time messaging
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=60, ping_interval=25, async_mode='threading')

# Initialize Mail
mail.init_app(app)

# Initialize Scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

DB_NAME = app.config['DB_NAME']


@app.context_processor
def inject_dev_quick_login():
    """
    Expose dev-only login credentials to templates.

    Returns None unless FLASK_ENV is not 'production', DEV_QUICK_LOGIN is on,
    and the credentials are present in the environment. See config.dev_quick_login.
    """
    from config import dev_quick_login
    try:
        return {'dev_quick_login': dev_quick_login()}
    except Exception:
        return {'dev_quick_login': None}


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
UPLOAD_FOLDER = 'static/uploads'
COMPANY_LOGOS_FOLDER = 'static/uploads/company_logos'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
if not os.path.exists(COMPANY_LOGOS_FOLDER):
    os.makedirs(COMPANY_LOGOS_FOLDER)

app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER



def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def normalize_profile_pic(profile_pic, name='User'):
    """
    Normalize profile picture path. If empty or invalid, return None
    to trigger fallback to ui-avatars in frontend
    """
    if not profile_pic or profile_pic == 'default.jpg' or profile_pic == '':
        return None
    if profile_pic.startswith('/'):
        return profile_pic
    return None

@app.template_filter('initials')
def get_initials(name):
    if not name:
        return '?'
    parts = name.split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[0].upper()

def send_email(to_email, subject, html_content):
    """
    Reliable email sending function with proper error handling
    Returns: (bool success, str message)
    """
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        sender_email = app.config['MAIL_USERNAME']
        sender_password = app.config['MAIL_PASSWORD']
        
        # Remove quotes from password if present
        if sender_password.startswith('"') and sender_password.endswith('"'):
            sender_password = sender_password[1:-1]
        if sender_password.startswith("'") and sender_password.endswith("'"):
            sender_password = sender_password[1:-1]
        
        print(f"\n🔧 Email Debug:")
        print(f"  From: {sender_email}")
        print(f"  To: {to_email}")
        print(f"  Subject: {subject}")
        print(f"  Server: {app.config['MAIL_SERVER']}:{app.config['MAIL_PORT']}")
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f'ALUMNI HUB <{app.config["MAIL_USERNAME"]}>'
        msg['To'] = to_email
        
        # Attach HTML
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # Send via SMTP
        print(f"  📤 Connecting to SMTP server...")
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT'], timeout=10) as server:
            server.starttls()
            print(f"  ✓ TLS connection established")
            
            server.login(sender_email, sender_password)
            print(f"  ✓ Authentication successful")
            
            server.send_message(msg)
            print(f"  ✓ Email sent successfully to {to_email}\n")
            
        return True, "Email sent successfully"
        
    except smtplib.SMTPAuthenticationError as e:
        error_msg = f"Email authentication failed. Please check MAIL_USERNAME and MAIL_PASSWORD in .env file. Error: {str(e)}"
        print(f"  ❌ {error_msg}\n")
        return False, error_msg
        
    except smtplib.SMTPException as e:
        error_msg = f"SMTP error while sending email: {str(e)}"
        print(f"  ❌ {error_msg}\n")
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Error sending email: {str(e)}"
        print(f"  ❌ {error_msg}\n")
        import traceback
        traceback.print_exc()
        return False, error_msg

def log_registration(conn, user_id, name, email, phone, role, enrollment_no=None,
                    employee_id=None, department=None, degree=None, pass_year=None,
                    company_name=None, designation=None, experience_years=None):
    """
    Log user registration to tracking table with role-specific details
    """
    try:
        c = conn.cursor()
        c.execute('''INSERT INTO registration_log
            (user_id, name, email, phone, role, enrollment_no, employee_id, department,
             degree, pass_year, company_name, designation, experience_years)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (user_id, name, email, phone, role, enrollment_no, employee_id, department,
             degree, pass_year, company_name, designation, experience_years))
        conn.commit()
        print(f"✓ Registration logged for {role}: {name} ({email})")
    except Exception as e:
        print(f"Error logging registration: {e}")


def update_user_activity(user_id, is_online=None, update_last_login=False):
    """Insert/update user activity details used in admin monitoring."""
    conn = None
    try:
        conn = get_db_connection()
        existing = conn.execute('SELECT user_id FROM user_activity WHERE user_id = ?', (user_id,)).fetchone()

        last_login_value = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if update_last_login else None
        status_value = None
        if is_online is not None:
            status_value = 'online' if is_online else 'offline'

        if existing:
            updates = []
            values = []
            if last_login_value is not None:
                updates.append('last_login = ?')
                values.append(last_login_value)
            if status_value is not None:
                updates.append('online_status = ?')
                values.append(status_value)

            if updates:
                values.append(user_id)
                conn.execute(f"UPDATE user_activity SET {', '.join(updates)} WHERE user_id = ?", tuple(values))
        else:
            conn.execute(
                '''
                INSERT INTO user_activity (user_id, last_login, online_status)
                VALUES (?, ?, ?)
                ''',
                (user_id, last_login_value, status_value or 'offline')
            )

        conn.commit()
    except Exception as e:
        logger.warning(f"Could not update user activity for user {user_id}: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- LOGIN SETUP ---
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, name, email, role, profile_pic, phone=None, is_verified=1, is_suspended=0, 
                 branch=None, passing_year=None, current_domain=None, skills=None, 
                 interests=None, city=None, company=None, bio=None):
        self.id = id
        self.name = name
        self.email = email
        self.role = role
        self.profile_pic = profile_pic
        self.phone = phone
        self.is_verified = is_verified
        self.is_suspended = is_suspended
        self.branch = branch
        self.passing_year = passing_year
        self.current_domain = current_domain
        self.skills = skills
        self.interests = interests
        self.city = city
        self.company = company
        self.bio = bio

    @property
    def is_active(self):
        return not self.is_suspended

@login_manager.user_loader
def load_user(user_id):
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if user:
            # Avatar generation logic
            avatar = user['profile_pic'] if user['profile_pic'] else f"https://ui-avatars.com/api/?name={user['name']}&background=0D6EFD&color=fff"
            is_verified = user['is_verified'] if 'is_verified' in user.keys() else 1
            
            def get_field(key):
                try:
                    return user[key]
                except (IndexError, KeyError):
                    return None

            return User(
                id=user['id'], name=user['name'], email=user['email'],
                role=user['role'], profile_pic=avatar, phone=user['phone'],
                is_verified=is_verified, is_suspended=get_field('is_suspended') or 0,
                branch=get_field('branch'), passing_year=get_field('passing_year'),
                current_domain=get_field('current_domain'), skills=get_field('skills'),
                interests=get_field('interests'), city=get_field('city'),
                company=get_field('company'), bio=get_field('bio')
            )
        return None
    except Exception as e:
        logger.error(f"Error loading user {user_id}: {e}")
        return None
    finally:
        if conn:
            conn.close()

# --- DATABASE SETUP ---
def init_db():
    """Initialize the database with all required tables"""
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Users table
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL,
                profile_pic TEXT,
                is_verified BOOLEAN DEFAULT 0,
                otp_code TEXT,
                is_approved BOOLEAN DEFAULT 1,
                is_suspended BOOLEAN DEFAULT 0,
                branch TEXT,
                passing_year INTEGER,
                current_domain TEXT,
                skills TEXT,
                interests TEXT,
                city TEXT,
                company TEXT,
                bio TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Migration: Add columns if they don't exist (for existing databases)
        columns_to_add = [
            ("is_verified", "BOOLEAN DEFAULT 0", "UPDATE users SET is_verified = 1"),
            ("is_approved", "BOOLEAN DEFAULT 1", "UPDATE users SET is_approved = 1"),
            ("is_suspended", "BOOLEAN DEFAULT 0", None),
            ("otp_code", "TEXT", None),
            ("branch", "TEXT", None),
            ("passing_year", "INTEGER", None),
            ("current_domain", "TEXT", None),
            ("skills", "TEXT", None),
            ("interests", "TEXT", None),
            ("city", "TEXT", None),
            ("company", "TEXT", None),
            ("bio", "TEXT", None)
        ]

        for col_name, col_def, update_sql in columns_to_add:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                if update_sql:
                    c.execute(update_sql)
                print(f"✓ Added {col_name} column to users")
            except sqlite3.OperationalError as e:
                if "duplicate column name" in str(e).lower():
                    pass # Column already exists
                else:
                    print(f"⚠ Warning adding {col_name}: {e}")
            except sqlite3.DatabaseError as e:
                # Backend-specific failures must not abort the whole bootstrap.
                print(f"⚠ Could not add {col_name}: {e}")

        # Student Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS student_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                enrollment_no TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                degree TEXT NOT NULL,
                semester INTEGER,
                cgpa REAL,
                skills TEXT,
                achievements TEXT,
                resume_link TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Alumni Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS alumni_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                enrollment_no TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                degree TEXT NOT NULL,
                pass_year INTEGER NOT NULL,
                company_name TEXT,
                designation TEXT,
                work_location TEXT,
                experience_years INTEGER,
                linkedin_url TEXT,
                achievements TEXT,
                bio TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Faculty Profile Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS faculty_profile (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                employee_id TEXT UNIQUE NOT NULL,
                department TEXT NOT NULL,
                designation TEXT NOT NULL,
                specialization TEXT,
                qualification TEXT,
                experience_years INTEGER,
                office_location TEXT,
                office_hours TEXT,
                bio TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Alumni Meet Registration Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS alumni_meet_registration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                full_name TEXT NOT NULL,
                gender TEXT,
                dob TEXT,
                contact_no TEXT NOT NULL,
                email TEXT NOT NULL,
                current_address TEXT,
                enrollment_no TEXT NOT NULL,
                course TEXT NOT NULL,
                passing_year INTEGER,
                current_status TEXT,
                company_name TEXT,
                designation TEXT,
                work_location TEXT,
                experience_years INTEGER,
                university_name TEXT,
                higher_study_course TEXT,
                higher_study_country TEXT,
                higher_study_state TEXT,
                enrollment_year INTEGER,
                contribute_to_college TEXT,
                contribution_areas TEXT,
                attending_meet TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Unified Connection Requests Table (Role-Agnostic)
        # Works for Student->Alumni, Student->Faculty, Alumni->Faculty, etc.
        c.execute('''
            CREATE TABLE IF NOT EXISTS connection_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accepted_at TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sender_id) REFERENCES users(id),
                FOREIGN KEY (receiver_id) REFERENCES users(id),
                UNIQUE(sender_id, receiver_id)
            )
        ''')

        # Migration: ensure accepted_at exists for older databases
        try:
            c.execute('ALTER TABLE connection_requests ADD COLUMN accepted_at TIMESTAMP')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e).lower():
                print(f"⚠ Warning adding accepted_at: {e}")

        # Migration: ensure updated_at exists for older databases
        try:
            c.execute('ALTER TABLE connection_requests ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP')
        except sqlite3.OperationalError as e:
            if 'duplicate column name' not in str(e).lower():
                print(f"⚠ Warning adding updated_at: {e}")

        # Unified Connections/Friends Table
        # Stores accepted friendships between any two users
        c.execute('''
            CREATE TABLE IF NOT EXISTS connections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id_1 INTEGER NOT NULL,
                user_id_2 INTEGER NOT NULL,
                connected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id_1) REFERENCES users(id),
                FOREIGN KEY (user_id_2) REFERENCES users(id),
                UNIQUE(user_id_1, user_id_2)
            )
        ''')

        # Registration Tracking Table - Logs all user registrations
        c.execute('''
            CREATE TABLE IF NOT EXISTS registration_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                role TEXT NOT NULL,
                enrollment_no TEXT,
                employee_id TEXT,
                department TEXT,
                degree TEXT,
                pass_year INTEGER,
                company_name TEXT,
                designation TEXT,
                experience_years INTEGER,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # Password Resets Table
        c.execute('''
            CREATE TABLE IF NOT EXISTS password_resets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT NOT NULL,
                otp TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # User activity used by admin monitoring
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                user_id INTEGER PRIMARY KEY,
                last_login TIMESTAMP,
                online_status TEXT DEFAULT 'offline',
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')

        # User Interactions Table — feeds ML recommendation engine
        c.execute('''
            CREATE TABLE IF NOT EXISTS user_interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                target_user_id INTEGER NOT NULL,
                interaction_type TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                FOREIGN KEY (target_user_id) REFERENCES users(id)
            )
        ''')

        # --- Performance Indexes ---
        index_statements = [
            'CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)',
            'CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)',
            'CREATE INDEX IF NOT EXISTS idx_users_created_at ON users(created_at)',
            'CREATE INDEX IF NOT EXISTS idx_connection_requests_receiver ON connection_requests(receiver_id, status)',
            'CREATE INDEX IF NOT EXISTS idx_connection_requests_sender ON connection_requests(sender_id, status)',
            'CREATE INDEX IF NOT EXISTS idx_connections_user1 ON connections(user_id_1)',
            'CREATE INDEX IF NOT EXISTS idx_connections_user2 ON connections(user_id_2)',
            'CREATE INDEX IF NOT EXISTS idx_user_interactions_user ON user_interactions(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_user_interactions_target ON user_interactions(target_user_id)',
            'CREATE INDEX IF NOT EXISTS idx_password_resets_email ON password_resets(email)',
            'CREATE INDEX IF NOT EXISTS idx_user_activity_last_login ON user_activity(last_login)',
            'CREATE INDEX IF NOT EXISTS idx_student_profile_user ON student_profile(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_alumni_profile_user ON alumni_profile(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_faculty_profile_user ON faculty_profile(user_id)',
            'CREATE INDEX IF NOT EXISTS idx_registration_log_user ON registration_log(user_id)',
        ]
        for idx_sql in index_statements:
            try:
                c.execute(idx_sql)
            except sqlite3.OperationalError:
                pass  # Table may not exist yet

        # Check if admin exists
        admin_exists = c.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]

        # Create Admin if not exists
        if admin_exists == 0:
            pw = generate_password_hash("admindbit195@")
            c.execute("INSERT INTO users (name, email, password, role, phone, is_verified) VALUES (?, ?, ?, ?, ?, ?)",
                      ("Super Admin", "admindbit195@college.edu", pw, "admin", "0000000000", 1))

        conn.commit()
        print("Database initialized successfully!")

        # ── Jobs table + migration-safe column additions ──────────────────────
        c.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                salary TEXT,
                job_type TEXT,
                apply_link TEXT,
                description TEXT,
                required_skills TEXT,
                posted_by INTEGER,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (posted_by) REFERENCES users(id) ON DELETE CASCADE
            )
        ''')
        jobs_cols_to_add = [
            ('company_name', 'TEXT'),
            ('company_website', 'TEXT'),
            ('company_logo', 'TEXT'),
            ('work_mode', 'TEXT'),
            ('employment_type', 'TEXT'),
            ('eligible_branch', 'TEXT'),
            ('eligible_batch', 'TEXT'),
            ('qualification', 'TEXT'),
            ('min_cgpa', 'TEXT'),
            ('experience_required', 'TEXT'),
            ('skills_required', 'TEXT'),
            ('skills_preferred', 'TEXT'),
            ('ctc_range', 'TEXT'),
            ('perks', 'TEXT'),
            ('deadline', 'TEXT'),
            ('joining_date', 'TEXT'),
            ('apply_method', 'TEXT'),
            ('openings', 'INTEGER DEFAULT 0'),
            ('selection_process', 'TEXT'),
            ('category', 'TEXT'),
            ('target_role', 'TEXT'),
            ('skill_level', 'TEXT'),
            ('job_status', "TEXT DEFAULT 'Open'"),
            # New columns for alumni/faculty job posting with admin approval
            ('approval_status', "TEXT DEFAULT 'approved'"),
            ('posted_by_role', 'TEXT'),
            ('rejection_reason', 'TEXT'),
        ]
        for col_name, col_def in jobs_cols_to_add:
            try:
                c.execute(f'ALTER TABLE jobs ADD COLUMN {col_name} {col_def}')
            except sqlite3.OperationalError as e:
                if 'duplicate column name' not in str(e).lower():
                    print(f"⚠ Warning adding jobs.{col_name}: {e}")
        # Backfill: jobs posted by admin before approval_status existed -> mark approved
        c.execute("""
            UPDATE jobs SET approval_status = 'approved'
            WHERE approval_status IS NULL OR approval_status = ''
        """)

        # Job applications (student -> job interest). This used to be created
        # only by scripts/migrate_jobs.py, so a fresh database - including a
        # Turso one - had no such table and applications failed at runtime.
        c.execute('''CREATE TABLE IF NOT EXISTS job_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER,
            student_id INTEGER,
            status TEXT DEFAULT 'applied',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
        )''')

        # Staged registrations awaiting OTP verification. Previously created
        # lazily inside the register route, which broke a cold start.
        # The column list MUST stay identical to the CREATE TABLE in the
        # register route, otherwise IF NOT EXISTS will never correct it.
        c.execute('''
            CREATE TABLE IF NOT EXISTS temp_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                phone TEXT NOT NULL,
                role TEXT NOT NULL,
                otp TEXT NOT NULL,
                profile_data TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                otp_expires_at TIMESTAMP
            )
        ''')

        conn.commit()

        # Messaging tables. These were previously only created by
        # scripts/init_messaging_db.py, so a fresh or Turso-backed database had
        # no messaging schema at all. Creating them here keeps the whole schema
        # self-migrating. Uses the same connection, so one commit covers both.
        from database.messaging_db import ensure_messaging_schema
        ensure_messaging_schema(conn)

        conn.commit()

    except sqlite3.Error as e:
        print(f"Database error: {e}")
        if conn:
            conn.rollback()
    except Exception as e:
        print(f"Initialization error: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

# --- RECOMMENDATION SYSTEM ---

# Recommendation logic and routes moved to models/recommendation.py and routes/recommendation_routes.py

# --- ROUTES ---

@app.route('/')
def home():
    return render_template('common/home.html')

@app.route('/about')
def about():
    return render_template('common/about.html')

@app.route('/services')
def services():
    return render_template('common/services.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            subject = request.form.get('subject', '').strip()
            message = request.form.get('message', '').strip()

            if not all([name, email, subject, message]):
                flash('All fields are required!', 'warning')
                return render_template('common/contact.html')

            # ===== SEND EMAIL TO ADMIN =====
            try:
                admin_email = os.getenv('ADMIN_EMAIL', 'alumnihub26@gmail.com')
                submission_time = datetime.now().strftime('%d %B %Y at %I:%M %p')

                # Email to admin using send_email function
                admin_html = f'''
                <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                    <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #f59e0b; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                        <h1 style="color: #f59e0b; margin: 0 0 15px 0; font-size: 1.8rem;">📨 New Contact Form Submission</h1>

                        <div style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #0ea5e9;">
                            <p style="margin: 0 0 8px 0; color: #0ea5e9; font-weight: 700; font-size: 0.9rem;">📱 ALUMNI HUB</p>
                            <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">Someone has sent you a contact message</p>
                        </div>
                    </div>

                    <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                        <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">👤 Sender Information</h3>

                        <table style="width: 100%; border-collapse: collapse;">
                            <tr style="border-bottom: 1px solid #e5e7eb;">
                                <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a; width: 30%;">Name:</td>
                                <td style="padding: 12px 0; color: #333;">{name}</td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e5e7eb;">
                                <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Email:</td>
                                <td style="padding: 12px 0; color: #333;"><a href="mailto:{email}" style="color: #0ea5e9; text-decoration: none; font-weight: 600;">{email}</a></td>
                            </tr>
                            <tr style="border-bottom: 1px solid #e5e7eb;">
                                <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Subject:</td>
                                <td style="padding: 12px 0; color: #333; font-weight: 600;">{subject}</td>
                            </tr>
                            <tr>
                                <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Submitted:</td>
                                <td style="padding: 12px 0; color: #666; font-size: 0.9rem;">{submission_time}</td>
                            </tr>
                        </table>
                    </div>

                    <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                        <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">💬 Message Content</h3>
                        <p style="margin: 0; color: #333; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{message}</p>
                    </div>

                    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white; text-align: center;">
                        <p style="margin: 0; font-size: 0.95rem; font-weight: 600;">Quick Reply</p>
                        <p style="margin: 10px 0 0 0; font-size: 0.85rem; opacity: 0.9;">Reply directly to this email or contact {name} at {email}</p>
                    </div>

                    <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                        <p style="margin: 0; color: #666; font-size: 0.85rem;">
                            <strong style="color: #1e3a8a;">Alumni Hub</strong> • Contact Management System<br>
                            This message was sent from the Alumni Hub contact form.
                        </p>
                    </div>
                </div>
                '''
                
                send_email(admin_email, f'📨 New Contact: {subject}', admin_html)
                # Email to user (confirmation)
                user_html = f'''
<div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
    <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #10b981; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
        <h1 style="color: #10b981; margin: 0 0 15px 0; font-size: 1.8rem;">✓ Message Received Successfully!</h1>
        <div style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #0ea5e9;">
            <p style="margin: 0 0 8px 0; color: #0ea5e9; font-weight: 700; font-size: 0.9rem;">📌 PROJECT</p>
            <p style="margin: 0; color: #1e3a8a; font-size: 1.2rem; font-weight: 800;">🎓 ALUMNI HUB MANAGEMENT SYSTEM</p>
            <p style="margin: 5px 0 0 0; color: #666; font-size: 0.85rem;">Your contact message has been submitted</p>
        </div>
    </div>
    <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
        <p style="color: #333; line-height: 1.8; margin: 0 0 15px 0;">Dear <strong>{name}</strong>,</p>
        <p style="color: #333; line-height: 1.8; margin: 0;">Thank you for reaching out to us through the Alumni Hub contact form! We have successfully received your message and appreciate you taking the time to get in touch with us.</p>
    </div>
    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(10, 150, 105, 0.08) 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #10b981; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
        <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">📋 Your Submission Details</h3>
        <table style="width: 100%; border-collapse: collapse;">
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 10px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a; width: 35%;">Subject:</td>
                <td style="padding: 10px 0; color: #333;">{subject}</td>
            </tr>
            <tr style="border-bottom: 1px solid #e5e7eb;">
                <td style="padding: 10px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Submitted On:</td>
                <td style="padding: 10px 0; color: #666; font-size: 0.95rem;">{submission_time}</td>
            </tr>
            <tr>
                <td style="padding: 10px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Source:</td>
                <td style="padding: 10px 0; color: #333; font-weight: 600;">🎓 Alumni Hub Contact Form</td>
            </tr>
        </table>
    </div>
    <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
        <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">⏱️ What's Next?</h3>
        <ul style="margin: 0; padding-left: 20px; color: #333; line-height: 1.8;">
            <li style="margin-bottom: 8px;">Our team will review your message</li>
            <li style="margin-bottom: 8px;">We'll respond within 24-48 business hours</li>
            <li style="margin-bottom: 8px;">Check your email for our reply</li>
            <li>If urgent, you can reach us directly</li>
        </ul>
    </div>
    <div style="background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white; text-align: center;">
        <p style="margin: 0; font-size: 0.95rem; font-weight: 600;">Contact Information</p>
        <p style="margin: 10px 0 0 0; font-size: 0.9rem; opacity: 0.95;">📧 alumnihubdbit195@outlook.com | 📞 +91-9876-543-210</p>
    </div>
    <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
        <p style="color: #333; margin: 0; line-height: 1.6; font-size: 0.95rem;">
            <strong style="color: #1e3a8a;">Alumni Hub</strong><br>
            <span style="color: #666; font-size: 0.9rem;">Building Connections, Creating Opportunities</span>
        </p>
        <p style="margin: 10px 0 0 0; color: #999; font-size: 0.85rem;">© 2026 Alumni Hub. All rights reserved.</p>
    </div>
</div>
                '''
                send_email(email, '✓ Message Received - Alumni Hub', user_html)

            except Exception as email_error:

                print(f"Email sending error: {email_error}")
                # Continue even if email fails

            flash('Thank you! We will get back to you soon.', 'success')
            return redirect(url_for('contact'))
        except Exception as e:
            flash('Error sending message. Please try again.', 'danger')

    return render_template('common/contact.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        conn = None
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()

            if user and check_password_hash(user['password'], password):
                # Helper to safely get user data even if columns are missing (though init_db should fix this)
                def get_user_field(key, default=None):
                    try:
                        return user[key]
                    except (IndexError, KeyError):
                        return default

                u_verified = get_user_field('is_verified', 1)
                u_approved = get_user_field('is_approved', 1)
                u_suspended = get_user_field('is_suspended', 0)
                u_role = get_user_field('role', 'student')

                # Check for Admin Approval (Alumni and Faculty require approval)
                if u_approved == 0 and u_role != 'admin':
                    flash('Your account is pending admin approval. Please wait for verification.', 'info')
                    return redirect(url_for('login'))

                # Check for Account Suspension
                if u_suspended == 1:
                    flash('Your account has been suspended by an admin for violation of community guidelines.', 'danger')
                    return redirect(url_for('login'))

                user_obj = User(
                    id=user['id'], name=user['name'], email=user['email'],
                    role=u_role, profile_pic=user['profile_pic'],
                    phone=user['phone'], is_verified=u_verified, is_suspended=u_suspended,
                    branch=get_user_field('branch'), passing_year=get_user_field('passing_year'),
                    current_domain=get_user_field('current_domain'), skills=get_user_field('skills'),
                    interests=get_user_field('interests'), city=get_user_field('city'),
                    company=get_user_field('company'), bio=get_user_field('bio')
                )
                login_user(user_obj)
                update_user_activity(user['id'], is_online=True, update_last_login=True)
                if u_role == 'admin':
                    return redirect(url_for('dashboard_admin'))
                if u_role == 'alumni':
                    return redirect(url_for('dashboard_alumni'))
                if u_role == 'faculty':
                    return redirect(url_for('dashboard_faculty'))
                return redirect(url_for('dashboard_student'))
            else:
                flash('Invalid Email or Password', 'danger')
        finally:
            if conn:
                conn.close()
    return render_template('auth/login.html')



@app.route('/register', methods=['GET', 'POST'])
def register():
    role = request.args.get('role', 'student')

    if request.method == 'POST':
        conn = None
        try:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()
            password = request.form.get('password', '')
            role = request.form.get('role', 'student')

            if not name or not email or not phone or not password:
                flash('Name, Email, Phone, and Password are required!', 'warning')
                return render_template('auth/register.html', role=role, form_data=request.form)

            # Strict Gmail Validation
            if not email.endswith('@gmail.com'):
                flash('Only Gmail addresses (ending in @gmail.com) are allowed.', 'warning')
                return render_template('auth/register.html', role=role, form_data=request.form)

            # Password Strength Validation
            if len(password) < 8:
                flash('Password must be at least 8 characters long.', 'warning')
                return render_template('auth/register.html', role=role, form_data=request.form)

            # Check if email already exists
            conn = get_db_connection()
            existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (email,)).fetchone()
            if existing_user:
                flash('Email already registered! Please login.', 'warning')
                return redirect(url_for('login'))

            password_hash = generate_password_hash(password)
            
            # Collect Role-Specific Data
            profile_data = {}
            missing_fields = []

            if role == 'student':
                profile_data['enrollment_no'] = request.form.get('stu_enrollment_no', request.form.get('enrollment_no', '')).strip()
                profile_data['department'] = request.form.get('stu_department', request.form.get('department', '')).strip()
                profile_data['degree'] = request.form.get('stu_degree', request.form.get('degree', '')).strip()
                profile_data['semester'] = request.form.get('stu_semester', request.form.get('semester', ''))
                
                if not profile_data['enrollment_no']: missing_fields.append('Enrollment No')
                if not profile_data['department']: missing_fields.append('Department')
                if not profile_data['degree']: missing_fields.append('Course/Degree')
                
                if missing_fields:
                    flash(f'Student details are incomplete: Missing {", ".join(missing_fields)}', 'warning')
                    return render_template('auth/register.html', role='student', form_data=request.form)

            elif role == 'alumni':
                profile_data['enrollment_no'] = request.form.get('alum_enrollment_no', request.form.get('enrollment_no', '')).strip()
                profile_data['department'] = request.form.get('alum_department', request.form.get('department', '')).strip()
                profile_data['degree'] = request.form.get('alum_degree', request.form.get('degree', '')).strip()
                profile_data['pass_year'] = request.form.get('alum_pass_year', request.form.get('pass_year', ''))
                profile_data['company_name'] = request.form.get('alum_company_name', request.form.get('company_name', ''))
                profile_data['designation'] = request.form.get('alum_designation', request.form.get('designation', ''))
                profile_data['experience_years'] = request.form.get('experience_years', '')

                if not profile_data['enrollment_no']: missing_fields.append('Enrollment No')
                if not profile_data['department']: missing_fields.append('Department')
                if not profile_data['degree']: missing_fields.append('Course/Degree')
                if not profile_data['pass_year']: missing_fields.append('Passing Year')

                if missing_fields:
                    flash(f'Alumni details are incomplete: Missing {", ".join(missing_fields)}', 'warning')
                    return render_template('auth/register.html', role='alumni', form_data=request.form)

            elif role == 'faculty':
                profile_data['employee_id'] = request.form.get('fac_employee_id', request.form.get('employee_id', '')).strip()
                profile_data['department'] = request.form.get('fac_department', request.form.get('department', '')).strip()
                profile_data['designation'] = request.form.get('fac_designation', request.form.get('designation', '')).strip()
                profile_data['qualification'] = request.form.get('fac_qualification', request.form.get('qualification', '')).strip()
                profile_data['experience_years'] = request.form.get('experience_years', '')

                if not profile_data['employee_id']: missing_fields.append('Employee ID')
                if not profile_data['department']: missing_fields.append('Department')
                if not profile_data['designation']: missing_fields.append('Designation')
                if not profile_data['qualification']: missing_fields.append('Qualification')

                if missing_fields:
                    flash(f'Faculty details are incomplete: Missing {", ".join(missing_fields)}', 'warning')
                    return render_template('auth/register.html', role='faculty', form_data=request.form)

            # Generate Secure 6-digit OTP
            otp = ''.join(secrets.choice(string.digits) for _ in range(6))

            # Store in temporary database table (temp_users)
            # First, create temp_users table if it doesn't exist
            conn.execute('''
                CREATE TABLE IF NOT EXISTS temp_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    phone TEXT NOT NULL,
                    role TEXT NOT NULL,
                    otp TEXT NOT NULL,
                    profile_data TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    otp_expires_at TIMESTAMP
                )
            ''')
            conn.commit()

            # Delete old temp entry if exists
            conn.execute('DELETE FROM temp_users WHERE email = ?', (email,))
            conn.commit()

            # Insert temporary user
            otp_expires = datetime.utcnow() + timedelta(minutes=2)
            import json
            conn.execute(
                '''INSERT INTO temp_users (name, email, password, phone, role, otp, profile_data, otp_expires_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, email, password_hash, phone, role, otp, json.dumps(profile_data), otp_expires)
            )
            conn.commit()
            
            # Send OTP Email
            html_content = f'''
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="background-color: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                        <div style="text-align: center; margin-bottom: 30px;">
                            <h2 style="color: #1e3a8a; margin: 0; font-size: 28px;">ALUMNI HUB</h2>
                            <p style="color: #666; font-size: 14px; margin: 5px 0 0 0;">Email Verification</p>
                        </div>
                        
                        <h3 style="color: #333; text-align: center; margin-top: 0;">Verify Your Email Address</h3>
                        
                        <p style="font-size: 16px; color: #333; line-height: 1.6;">
                            Welcome to Alumni Hub! Please use the following One-Time Password (OTP) to verify your email address. Your account will be created upon verification.
                        </p>
                        
                        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 5px; text-align: center; margin: 30px 0; border-left: 4px solid #0ea5e9;">
                            <p style="margin: 0; color: #666; font-size: 14px;">Your OTP Code:</p>
                            <h1 style="color: #0ea5e9; letter-spacing: 5px; margin: 10px 0; font-size: 32px; font-family: 'Courier New', monospace;">{otp}</h1>
                            <p style="margin: 0; color: #999; font-size: 12px;">This code is valid for 2 minutes.</p>
                        </div>
                        
                        <div style="background-color: #fff3cd; border-left: 4px solid #ffc107; padding: 15px; border-radius: 5px; margin: 20px 0;">
                            <p style="color: #856404; font-size: 13px; margin: 0;">
                                <strong>Security Note:</strong> Never share this OTP with anyone. ALUMNI HUB staff will never ask for your OTP.
                            </p>
                        </div>
                        
                        <p style="color: #666; font-size: 14px; line-height: 1.6;">
                            If you did not create a ALUMNI HUB account, please ignore this email.
                        </p>
                        
                        <div style="border-top: 1px solid #eee; margin-top: 30px; padding-top: 20px; text-align: center; color: #999; font-size: 12px;">
                            <p style="margin: 0;">© 2024 ALUMNI HUB. All rights reserved.</p>
                        </div>
                    </div>
                </body>
            </html>
            '''
            
            # Send email using new function
            email_sent, email_message = send_email(email, 'Verify Your Email - ALUMNI HUB', html_content)
            
            if email_sent:
                flash(f'✓ Verification code sent to {email}. Please check your email and enter the OTP.', 'success')
                return redirect(url_for('verify_otp', email=email))
            else:
                # Still redirect even if email fails (for testing)
                logger.warning(f'Email failed for {email}: {email_message}. OTP: {otp}')
                flash('⚠ Verification code could not be emailed. Please contact admin or try again.', 'warning')
                return redirect(url_for('verify_otp', email=email))

        except Exception as e:
            print(f"Registration error: {e}")
            flash(f'Registration error: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()

    return render_template('auth/register.html', role=role)

@app.route('/logout')
@login_required
def logout():
    try:
        update_user_activity(current_user.id, is_online=False, update_last_login=False)
    except Exception:
        pass
    logout_user()
    return redirect(url_for('home'))

@app.route('/verify-otp', methods=['GET', 'POST'])
def verify_otp():
    email = request.args.get('email') or request.form.get('email')
    
    if request.method == 'GET':
        return render_template('auth/verify_otp.html', email=email)
    
    if request.method == 'POST':
        otp = request.form.get('otp', '').strip()
        conn = None
        
        try:
            conn = get_db_connection()
            
            # Check temp_users table for registration OTP
            temp_user = conn.execute('SELECT * FROM temp_users WHERE email = ?', (email,)).fetchone()
            
            if temp_user:
                # Check OTP expiry
                otp_expiry = datetime.fromisoformat(temp_user['otp_expires_at'])
                if datetime.utcnow() > otp_expiry:
                    # Delete expired OTP
                    conn.execute('DELETE FROM temp_users WHERE email = ?', (email,))
                    conn.commit()
                    flash('OTP has expired! Please register again.', 'danger')
                    return render_template('auth/verify_otp.html', email=email)
                
                # Verify OTP
                if temp_user['otp'] != otp:
                    flash('Invalid OTP! Please try again.', 'danger')
                    return render_template('auth/verify_otp.html', email=email)
                
                # OTP is correct - create actual user account
                import json
                profile_data = json.loads(temp_user['profile_data']) if temp_user['profile_data'] else {}
                
                # Determine approval status (Alumni & Faculty need approval)
                is_approved = 1 if temp_user['role'] not in ['alumni', 'faculty'] else 0
                
                try:
                    c = conn.cursor()
                    
                    # Double check if user already exists (to prevent race conditions)
                    existing_user = conn.execute('SELECT id FROM users WHERE email = ?', (temp_user['email'],)).fetchone()
                    
                    if existing_user:
                        user_id = existing_user['id']
                        # User exists, maybe from a previous interrupted registration. 
                        # Just update password and verified status if needed.
                        c.execute('''UPDATE users SET password = ?, is_verified = 1, is_approved = ? 
                                     WHERE id = ?''', 
                                  (temp_user['password'], is_approved, user_id))
                    else:
                        # Insert user into main users table
                        c.execute('''INSERT INTO users (name, email, password, phone, role, is_verified, is_approved, otp_code)
                                     VALUES (?, ?, ?, ?, ?, 1, ?, NULL)''',
                                 (temp_user['name'], temp_user['email'], temp_user['password'], 
                                  temp_user['phone'], temp_user['role'], is_approved))
                        user_id = c.lastrowid
                    
                    conn.commit()
                    
                    # Insert role-specific profile data
                    if temp_user['role'] == 'student':
                        # Use INSERT OR REPLACE to handle cases where profile might already exist
                        c.execute('''INSERT OR REPLACE INTO student_profile 
                                    (user_id, enrollment_no, department, degree, semester)
                                    VALUES (?, ?, ?, ?, ?)''',
                                (user_id, profile_data.get('enrollment_no'), profile_data.get('department'),
                                 profile_data.get('degree'), profile_data.get('semester')))
                        
                    elif temp_user['role'] == 'alumni':
                        c.execute('''INSERT OR REPLACE INTO alumni_profile
                                    (user_id, enrollment_no, department, degree, pass_year, company_name, designation)
                                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                                (user_id, profile_data.get('enrollment_no'), profile_data.get('department'),
                                 profile_data.get('degree'), profile_data.get('pass_year'),
                                 profile_data.get('company_name'), profile_data.get('designation')))
                        
                    elif temp_user['role'] == 'faculty':
                        c.execute('''INSERT OR REPLACE INTO faculty_profile
                                    (user_id, employee_id, department, designation, qualification)
                                    VALUES (?, ?, ?, ?, ?)''',
                                (user_id, profile_data.get('employee_id'), profile_data.get('department'),
                                 profile_data.get('designation'), profile_data.get('qualification')))
                    
                    conn.commit()
                    
                    # Delete from temp_users
                    conn.execute('DELETE FROM temp_users WHERE email = ?', (email,))
                    conn.commit()
                    
                    # Auto-login if approved, else redirect to login
                    if is_approved:
                        user_obj = User(
                            id=user_id, name=temp_user['name'], email=temp_user['email'],
                            role=temp_user['role'], profile_pic=None,
                            phone=temp_user['phone'], is_verified=1
                        )
                        login_user(user_obj)
                        flash('✓ Email verified! Account created successfully. Welcome!', 'success')
                        
                        if temp_user['role'] == 'student':
                            return redirect(url_for('dashboard_student'))
                        elif temp_user['role'] == 'alumni':
                            return redirect(url_for('dashboard_alumni'))
                        elif temp_user['role'] == 'faculty':
                            return redirect(url_for('dashboard_faculty'))
                        elif temp_user['role'] == 'admin':
                            return redirect(url_for('dashboard_admin'))
                        else:
                            return redirect(url_for('home'))
                    else:
                        flash('✓ Email verified! Your account is pending admin approval. Please wait.', 'info')
                        return redirect(url_for('login'))
                        
                except Exception as e:
                    conn.rollback()
                    print(f"Error creating user account: {e}")
                    import traceback
                    traceback.print_exc()
                    flash(f'Error creating account: {str(e)}', 'danger')
                    return render_template('auth/verify_otp.html', email=email)
            else:
                flash('No registration found for this email. Please register first.', 'danger')
                return render_template('auth/verify_otp.html', email=email)
                
        except Exception as e:
            print(f"OTP Verification Error: {e}")
            import traceback
            traceback.print_exc()
            flash(f'An error occurred: {str(e)}', 'danger')
            return render_template('auth/verify_otp.html', email=email)
        finally:
            if conn:
                conn.close()

@app.route('/resend-otp', methods=['POST'])
def resend_otp():
    email = request.form.get('email')
    conn = None
    
    try:
        conn = get_db_connection()
        
        # Check temp_users table first (new registration flow)
        temp_user = conn.execute('SELECT * FROM temp_users WHERE email = ?', (email,)).fetchone()
        
        if temp_user:
            # Generate new OTP for temporary registration
            new_otp = ''.join(secrets.choice(string.digits) for _ in range(6))
            otp_expires = datetime.utcnow() + timedelta(minutes=2)
            
            conn.execute('UPDATE temp_users SET otp = ?, otp_expires_at = ? WHERE email = ?',
                        (new_otp, otp_expires, email))
            conn.commit()
            
            html_content = f'''
            <html>
                <body style="font-family: Arial, sans-serif; padding: 20px; background-color: #f4f4f4;">
                    <div style="background-color: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: 0 auto;">
                        <h2 style="color: #1e3a8a; text-align: center;">Verify Your Email</h2>
                        <p style="font-size: 16px; color: #333;">Here is your new One-Time Password (OTP):</p>
                        <div style="background-color: #f0f9ff; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0; border-left: 4px solid #0ea5e9;">
                            <h1 style="color: #0ea5e9; letter-spacing: 5px; margin: 0; font-family: 'Courier New', monospace; font-size: 32px;">{new_otp}</h1>
                            <p style="margin: 10px 0 0 0; color: #999; font-size: 12px;">Valid for 2 minutes.</p>
                        </div>
                    </div>
                </body>
            </html>
            '''
            
            email_sent, msg_text = send_email(email, 'Resend: Verify Your Email - Alumni Hub', html_content)
            
            if email_sent:
                flash('✓ Verification code resent successfully!', 'success')
            else:
                logger.warning(f'Resend email failed for {email}: {msg_text}. OTP: {new_otp}')
                flash('⚠ Could not send OTP email. Please contact admin or try again.', 'warning')
            
            return render_template('auth/verify_otp.html', email=email)
        else:
            flash('No registration found for this email.', 'danger')
            return render_template('auth/verify_otp.html', email=email)
            
    except Exception as e:
        print(f"Error resending OTP: {e}")
        flash('Failed to resend OTP. Please try again.', 'danger')
        return render_template('auth/verify_otp.html', email=email)
    finally:
        if conn:
            conn.close()

# --- PROFILE ROUTES ---

@app.route('/profile')
@login_required
def profile():
    if current_user.role == 'student':
        return redirect(url_for('student_profile', user_id=current_user.id))
    elif current_user.role == 'alumni':
        return redirect(url_for('alumni_profile', user_id=current_user.id))
    elif current_user.role == 'faculty':
        return redirect(url_for('faculty_profile', user_id=current_user.id))
    elif current_user.role == 'admin':
        return redirect(url_for('admin_profile', user_id=current_user.id))
    return redirect(url_for('home'))

@app.route('/student/profile/<int:user_id>')
@login_required
def student_profile(user_id):
    if current_user.role not in ['admin', 'student', 'faculty']:
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user or not profile:
            flash('Student not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('student/profile.html', user=user, profile=profile)
    finally:
        if conn:
            conn.close()

@app.route('/alumni/profile/<int:user_id>')
@login_required
def alumni_profile(user_id):
    if current_user.role not in ['admin', 'alumni', 'student', 'faculty']:
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user or not profile:
            flash('Alumni not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('alumni/profile.html', user=user, profile=profile)
    finally:
        if conn:
            conn.close()

@app.route('/faculty/profile/<int:user_id>')
@login_required
def faculty_profile(user_id):
    if current_user.role not in ['admin', 'student', 'alumni', 'faculty']:
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user:
            flash('Faculty not found!', 'danger')
            return redirect(url_for('home'))

        # If profile doesn't exist, create a default one
        if not profile:
            try:
                conn.execute('''INSERT INTO faculty_profile
                    (user_id, employee_id, department, designation, specialization, qualification, experience_years, office_location, office_hours, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, f'FAC{user_id}', 'N/A', 'Faculty', '', '', 0, '', '', ''))
                conn.commit()
                profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()
            except Exception as e:
                print(f"Error creating faculty profile: {e}")
                profile = None

        return render_template('faculty/profile.html', user=user, profile=profile)
    except Exception as e:
        print(f"Faculty profile error: {e}")
        flash('Error loading profile!', 'danger')
        return redirect(url_for('home'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/profile/<int:user_id>')
@login_required
def admin_profile(user_id):
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user or user['role'] != 'admin':
            flash('Admin not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('admin/profile_admin.html', user=user)
    except Exception as e:
        print(f"Admin profile error: {e}")
        flash('Error loading profile!', 'danger')
        return redirect(url_for('home'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/users/<role>')
@login_required
def admin_view_users(role):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        if role == 'all':
            users = conn.execute('SELECT * FROM users ORDER BY id DESC').fetchall()
        else:
            users = conn.execute('SELECT * FROM users WHERE role = ? ORDER BY id DESC', (role,)).fetchall()
        return render_template('admin/admin_view_users.html', users=users, role=role)
    finally:
        if conn:
            conn.close()

@app.route('/admin/approve-requests')
@login_required
def admin_approve_requests():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        # Fetch pending users (is_approved = 0)
        users = conn.execute('SELECT * FROM users WHERE is_approved = 0 ORDER BY created_at DESC').fetchall()
        return render_template('admin/admin_view_users.html', users=users, role='pending')
    finally:
        if conn:
            conn.close()



# --- DASHBOARDS ---

@app.route('/student/dashboard')
@login_required
def dashboard_student():
    if current_user.role not in ('student', 'admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    conn = None
    try:
        conn = get_db_connection()

        # Fetch alumni with all details
        alumni = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone,
                   a.enrollment_no, a.department, a.degree, a.pass_year,
                   a.company_name, a.designation, a.work_location, a.experience_years
            FROM users u
            JOIN alumni_profile a ON u.id = a.user_id
            WHERE u.role='alumni'
            ORDER BY a.pass_year DESC
        """).fetchall()

        # Fetch faculty members
        faculty = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone,
                   f.department, f.designation, f.office_location
            FROM users u
            JOIN faculty_profile f ON u.id = f.user_id
            WHERE u.role='faculty'
            ORDER BY f.department
        """).fetchall()

        # Get current student profile
        student = conn.execute(
            'SELECT * FROM student_profile WHERE user_id = ?',
            (current_user.id,)
        ).fetchone()

        # Get pending connection requests
        pending_requests = conn.execute("""
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """, (current_user.id,)).fetchall()

        # Fetch other students for the directory
        other_students = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   s.department, s.degree, s.semester
            FROM users u
            LEFT JOIN student_profile s ON u.id = s.user_id
            WHERE u.role='student' AND u.id != ?
            ORDER BY u.name ASC
        """, (current_user.id,)).fetchall()

        # Fetch recommendations
        recommendations = get_recommended_users(current_user)

        return render_template('student/dashboard.html',
                             alumni=alumni,
                             faculty=faculty,
                             student=student,
                             other_students=other_students,
                             pending_requests=pending_requests,
                             pending_count=len(pending_requests),
                             recommendations=recommendations)
    finally:
        if conn:
            conn.close()

@app.route('/alumni/dashboard')
@login_required
def dashboard_alumni():
    if current_user.role not in ('alumni', 'admin'):
        flash('Access denied.', 'danger')
        return redirect(url_for('home'))
    conn = None
    try:
        conn = get_db_connection()

        # Get pending connection requests
        pending_requests = conn.execute("""
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """, (current_user.id,)).fetchall()

        # Get alumni profile for completeness tracking
        alumni_profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (current_user.id,)).fetchone()

        # Fetch recommendations
        recommendations = get_recommended_users(current_user)

        return render_template('alumni/dashboard.html',
                             pending_requests=pending_requests,
                             pending_count=len(pending_requests),
                             alumni=alumni_profile,
                             recommendations=recommendations)
    finally:
        if conn:
            conn.close()

@app.route('/faculty/dashboard')
@login_required
def dashboard_faculty():
    if current_user.role != 'faculty':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (current_user.id,)).fetchone()

        # If profile doesn't exist, create a default one or redirect to complete profile
        if not profile:
            # Try to create a default profile if it doesn't exist
            try:
                conn.execute('''INSERT INTO faculty_profile
                    (user_id, employee_id, department, designation, specialization, qualification, experience_years, office_location, office_hours, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (current_user.id, f'FAC{current_user.id}', 'N/A', 'Faculty', '', '', 0, '', '', ''))
                conn.commit()
                profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (current_user.id,)).fetchone()
            except Exception as e:
                print(f"Error creating default faculty profile: {e}")
                # If still no profile, redirect to edit profile page
                return redirect(url_for('edit_faculty_profile', user_id=current_user.id))

        # Get pending connection requests
        pending_requests = conn.execute("""
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        """, (current_user.id,)).fetchall()

        # Fetch alumni for directory
        alumni = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   a.enrollment_no, a.department, a.degree, a.pass_year,
                   a.company_name, a.designation, a.work_location, a.experience_years
            FROM users u
            JOIN alumni_profile a ON u.id = a.user_id
            WHERE u.role='alumni'
            ORDER BY a.pass_year DESC
        """).fetchall()

        # Fetch all students for directory
        students = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   s.department, s.degree, s.semester, s.skills, s.cgpa
            FROM users u
            JOIN student_profile s ON u.id = s.user_id
            WHERE u.role='student'
            ORDER BY u.name ASC
        """).fetchall()

        # Fetch other faculty members (colleagues)
        faculty_members = conn.execute("""
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   f.department, f.designation, f.office_location, f.specialization
            FROM users u
            JOIN faculty_profile f ON u.id = f.user_id
            WHERE u.role='faculty' AND u.id != ?
            ORDER BY f.department
        """, (current_user.id,)).fetchall()

        return render_template('faculty/dashboard.html',
                             profile=profile,
                             pending_requests=pending_requests,
                             pending_count=len(pending_requests),
                             alumni=alumni,
                             students=students,
                             faculty=faculty_members)

    except Exception as e:
        print(f"Dashboard faculty error: {e}")
        flash('Error loading dashboard!', 'danger')
        return redirect(url_for('home'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/dashboard')
@login_required
def dashboard_admin():
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        
        # Fetch users with their profile data (department, batch/pass_year)
        users_query = """
            SELECT 
                u.id, u.name, u.email, u.role, u.created_at, u.profile_pic,
                COALESCE(s.department, a.department, f.department, 'N/A') as department,
                COALESCE(s.semester, a.pass_year, NULL) as batch_info,
                u.role as user_role
            FROM users u
            LEFT JOIN student_profile s ON u.id = s.user_id AND u.role = 'student'
            LEFT JOIN alumni_profile a ON u.id = a.user_id AND u.role = 'alumni'
            LEFT JOIN faculty_profile f ON u.id = f.user_id AND u.role = 'faculty'
            ORDER BY u.id DESC
        """
        users = conn.execute(users_query).fetchall()
        
        # Optimized: Single GROUP BY query instead of 3 separate COUNT queries
        role_counts_raw = conn.execute(
            "SELECT role, COUNT(*) as cnt FROM users GROUP BY role"
        ).fetchall()
        role_counts = {row['role']: row['cnt'] for row in role_counts_raw}
        a_count = role_counts.get('alumni', 0)
        s_count = role_counts.get('student', 0)
        f_count = role_counts.get('faculty', 0)
        
        # Dynamic Chart Data Calculation
        current_year = datetime.now().year
        years = [str(y) for y in range(current_year - 4, current_year + 1)]
        
        # Optimized: Single query for all yearly role counts instead of 15+ queries in a loop
        yearly_raw = conn.execute("""
            SELECT strftime('%Y', created_at) as year, role, COUNT(*) as cnt
            FROM users
            WHERE strftime('%Y', created_at) >= ?
            GROUP BY year, role
        """, (years[0],)).fetchall()
        yearly_map = {}
        for row in yearly_raw:
            yearly_map.setdefault(row['year'], {})[row['role']] = row['cnt']
        
        students_data = [yearly_map.get(y, {}).get('student', 0) for y in years]
        alumni_data = [yearly_map.get(y, {}).get('alumni', 0) for y in years]
        faculty_data = [yearly_map.get(y, {}).get('faculty', 0) for y in years]
        
        # Event registrations by year (single query)
        try:
            events_raw = conn.execute("""
                SELECT strftime('%Y', created_at) as year, COUNT(*) as cnt
                FROM alumni_meet_registration
                WHERE strftime('%Y', created_at) >= ?
                GROUP BY year
            """, (years[0],)).fetchall()
            events_map = {row['year']: row['cnt'] for row in events_raw}
        except sqlite3.OperationalError:
            events_map = {}
        events_data = [events_map.get(y, 0) for y in years]

        chart_data = {
            'years': years,
            'students': students_data,
            'alumni': alumni_data,
            'faculty': faculty_data
        }
        
        # Total event registrations for stat card
        event_total = sum(events_data)
        
        return render_template('admin/dashboard_admin.html', 
                               users=users, 
                               a_count=a_count, 
                               s_count=s_count, 
                               f_count=f_count, 
                               event_total=event_total,
                               chart_data=chart_data)
    finally:
        if conn:
            conn.close()

# --- ALUMNI MEET ROUTES ---

# --- MESSAGING ROUTES ---

# Removed - /messages route moved to student-specific section


@app.route('/chat/<int:other_user_id>')
@login_required
def private_chat(other_user_id):
    """Display private chat with another user"""
    conn = None
    try:
        conn = get_db_connection()

        # Get other user details
        other_user = conn.execute('SELECT id, name, email, role, phone, profile_pic FROM users WHERE id = ?',
                              (other_user_id,)).fetchone()

        if not other_user:
            flash('User not found', 'danger')
            return redirect(url_for('messages'))

        # Verify users are connected before allowing chat
        is_connected = conn.execute('''
            SELECT 1 FROM connections 
            WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        ''', (current_user.id, other_user_id, other_user_id, current_user.id)).fetchone()

        if not is_connected and current_user.role != 'admin':
            flash('You must be connected to chat with this user.', 'warning')
            return redirect(url_for('messages'))

        return render_template('messaging/private_chat.html',
                             other_user_id=other_user_id,
                             other_user_name=other_user['name'],
                             other_user_role=other_user['role'],
                             other_user_phone=other_user['phone'],
                             other_user_pic=other_user['profile_pic'])
    finally:
        if conn:
            conn.close()


@app.route('/admin/messaging-control')
@login_required
def admin_messaging_control():
    """Admin messaging control panel"""
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard_admin'))

    return render_template('admin/admin_messaging_control.html')


@app.route('/admin/connection-monitor')
@login_required
def admin_connection_monitor():
    """Admin dashboard for monitoring connection request/activity details."""
    if current_user.role != 'admin':
        flash('Unauthorized access', 'danger')
        return redirect(url_for('dashboard_admin'))

    role_filter = request.args.get('role', 'all').strip().lower()
    if role_filter not in ('all', 'student', 'alumni'):
        role_filter = 'all'

    search = request.args.get('search', '').strip()

    conn = None
    try:
        conn = get_db_connection()
        records = get_connection_activity(conn, role_filter=role_filter, search=search)
        return render_template(
            'admin/connection_monitor.html',
            records=records,
            role_filter=role_filter,
            search=search,
            total_records=len(records),
        )
    except Exception as e:
        logger.error(f"Error loading admin connection monitor: {e}")
        flash('Could not load connection monitoring data.', 'danger')
        return redirect(url_for('dashboard_admin'))
    finally:
        if conn:
            conn.close()


@app.route('/admin/connection-monitor/user/<int:user_id>')
@login_required
def admin_connection_monitor_user(user_id):
    """Return complete user profile/activity data for admin modal view."""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = None
    try:
        conn = get_db_connection()
        row = conn.execute(
            '''
            SELECT
                u.id,
                u.name,
                u.role,
                u.email,
                COALESCE(sp.department, ap.department, fp.department, u.branch, 'N/A') AS department,
                COALESCE(sp.skills, u.skills, '') AS skills,
                COALESCE(u.current_domain, '') AS current_domain,
                COALESCE(sp.semester, ap.pass_year, u.passing_year) AS passing_year,
                COALESCE(ap.company_name, u.company, '') AS current_company,
                ua.last_login,
                COALESCE(ua.online_status, 'offline') AS online_status
            FROM users u
            LEFT JOIN student_profile sp ON sp.user_id = u.id AND u.role = 'student'
            LEFT JOIN alumni_profile ap ON ap.user_id = u.id AND u.role = 'alumni'
            LEFT JOIN faculty_profile fp ON fp.user_id = u.id AND u.role = 'faculty'
            LEFT JOIN user_activity ua ON ua.user_id = u.id
            WHERE u.id = ?
            ''',
            (user_id,),
        ).fetchone()

        if not row:
            return jsonify({'error': 'User not found'}), 404

        stats = get_user_statistics(conn, user_id)

        try:
            msg_row = conn.execute(
                '''
                SELECT COUNT(*) AS message_count
                FROM private_messages
                WHERE sender_id = ? OR receiver_id = ?
                ''',
                (user_id, user_id),
            ).fetchone()
            message_count = msg_row['message_count'] if msg_row else 0
        except Exception:
            message_count = 0

        payload = dict(row)
        payload.update(stats)
        payload['messages_exchanged'] = message_count

        return jsonify({'user': payload}), 200
    except Exception as e:
        logger.error(f"Error loading monitor profile for user {user_id}: {e}")
        return jsonify({'error': 'Failed to load user profile'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/alumni/meet/register', methods=['GET', 'POST'])
@login_required
def alumni_meet_register():
    if current_user.role != 'alumni':
        flash('Only alumni can register for the meet!', 'warning')
        return redirect(url_for('home'))

    if request.method == 'POST':
        conn = None
        try:
            full_name = request.form.get('full_name', '').strip()
            gender = request.form.get('gender', '')
            dob = request.form.get('dob', '')
            contact_no = request.form.get('contact_no', '').strip()
            email = request.form.get('email', '').strip()
            current_address = request.form.get('current_address', '').strip()
            enrollment_no = request.form.get('enrollment_no', '').strip()
            course = request.form.get('course', '')
            passing_year = request.form.get('passing_year', '')
            current_status = request.form.get('current_status', '')
            company_name = request.form.get('company_name', '')
            designation = request.form.get('designation', '')
            work_location = request.form.get('work_location', '')
            experience_years = request.form.get('experience_years', '')
            university_name = request.form.get('university_name', '')
            higher_study_course = request.form.get('higher_study_course', '')
            higher_study_country = request.form.get('higher_study_country', '')
            higher_study_state = request.form.get('higher_study_state', '')
            enrollment_year = request.form.get('enrollment_year', '')
            contribute_to_college = request.form.get('contribute_to_college', 'No')
            contribution_areas = ','.join(request.form.getlist('contribution_areas'))
            attending_meet = request.form.get('attending_meet', 'No')

            if not all([full_name, contact_no, email, enrollment_no, course, passing_year]):
                flash('Please fill in all required fields!', 'warning')
                return render_template('alumni/meet_register.html')

            conn = get_db_connection()
            conn.execute('''INSERT INTO alumni_meet_registration
                (user_id, full_name, gender, dob, contact_no, email, current_address,
                 enrollment_no, course, passing_year, current_status, company_name,
                 designation, work_location, experience_years, university_name,
                 higher_study_course, higher_study_country, higher_study_state,
                 enrollment_year, contribute_to_college, contribution_areas, attending_meet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                (current_user.id, full_name, gender, dob, contact_no, email, current_address,
                 enrollment_no, course, passing_year, current_status, company_name,
                 designation, work_location, experience_years, university_name,
                 higher_study_course, higher_study_country, higher_study_state,
                 enrollment_year, contribute_to_college, contribution_areas, attending_meet))
            conn.commit()

            flash('Alumni Meet Registration Successful!', 'success')
            return redirect(url_for('dashboard_alumni'))
        except sqlite3.IntegrityError:
            if conn:
                conn.rollback()
            flash('You have already registered for this meet!', 'warning')
        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Alumni meet registration error: {e}")
            flash(f'Error during registration: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()

    return render_template('alumni/meet_register.html')

@app.route('/alumni/meet/view')
@login_required
def alumni_meet_view():
    if current_user.role != 'alumni':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        registration = conn.execute('SELECT * FROM alumni_meet_registration WHERE user_id = ?',
                                   (current_user.id,)).fetchone()

        if not registration:
            flash('You have not registered for the Alumni Meet yet!', 'info')
            return redirect(url_for('alumni_meet_register'))

        return render_template('alumni/meet_view.html', registration=registration)
    finally:
        if conn:
            conn.close()

# --- ALUMNI FEATURE ROUTES ---

@app.route('/alumni/network')
@login_required
def alumni_network():
    if current_user.role != 'alumni': return redirect(url_for('home'))
    return render_template('alumni/network.html')

@app.route('/alumni/messages')
@login_required
def alumni_messages():
    if current_user.role != 'alumni': return redirect(url_for('home'))
    return render_template('alumni/messages.html')

@app.route('/alumni/mentorship')
@login_required
def alumni_mentorship():
    if current_user.role != 'alumni': return redirect(url_for('home'))
    return render_template('alumni/mentorship.html')

@app.route('/alumni/post-job')
@login_required
def alumni_post_job():
    # Redirect to unified post-job route (supports both alumni and faculty)
    return redirect(url_for('post_job'))

@app.route('/alumni/jobs')
@login_required
def alumni_jobs():
    if current_user.role not in ('alumni', 'faculty'): return redirect(url_for('home'))
    conn = None
    try:
        conn = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')
        active_jobs = conn.execute('''
            SELECT j.*, u.name as posted_by_name 
            FROM jobs j 
            LEFT JOIN users u ON j.posted_by = u.id 
            WHERE j.is_active = 1
              AND (j.approval_status = 'approved' OR j.approval_status IS NULL)
              AND (j.deadline IS NULL OR j.deadline = '' OR j.deadline >= ?)
            ORDER BY j.created_at DESC
        ''', (today,)).fetchall()
        previous_jobs = conn.execute('''
            SELECT j.*, u.name as posted_by_name 
            FROM jobs j 
            LEFT JOIN users u ON j.posted_by = u.id 
            WHERE j.is_active = 1
              AND (j.approval_status = 'approved' OR j.approval_status IS NULL)
              AND j.deadline IS NOT NULL AND j.deadline != '' AND j.deadline < ?
            ORDER BY j.deadline DESC
        ''', (today,)).fetchall()
        recommended = get_recommended_jobs(current_user)
        return render_template('alumni/jobs.html', jobs=active_jobs, previous_jobs=previous_jobs, recommended=recommended)
    finally:
        if conn:
            conn.close()

@app.route('/alumni/spotlight')
@login_required
def alumni_spotlight():
    if current_user.role != 'alumni': return redirect(url_for('home'))
    return render_template('alumni/spotlight.html')

@app.route('/alumni/events')
@login_required
def alumni_events():
    if current_user.role != 'alumni': return redirect(url_for('home'))
    return render_template('alumni/events.html')

@app.route('/alumni/notifications')
@login_required
def alumni_notifications():
    if current_user.role != 'alumni': return redirect(url_for('home'))
    return render_template('alumni/notifications.html')

@app.route('/alumni/settings')
@login_required
def alumni_settings():
    if current_user.role != 'alumni': return redirect(url_for('home'))
    return render_template('alumni/settings.html')

# --- PROFILE EDIT ROUTES ---

@app.route('/student/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_student_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            cgpa = request.form.get('cgpa', '')
            skills = request.form.get('skills', '').strip()
            achievements = request.form.get('achievements', '').strip()
            resume_link = request.form.get('resume_link', '').strip()
            semester = request.form.get('semester', '')

            # Client-side validation already happens, so only save if data is valid
            # This is a backup validation
            if not name or not phone:
                # Don't redirect - keep form intact by re-rendering
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                profile = conn.execute('SELECT * FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()
                flash('Name and Phone are required!', 'warning')
                return render_template('student/edit_profile.html', user=user, profile=profile)

            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"student_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"

            # Update users table
            if profile_pic:
                conn.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?',
                            (name, phone, user_id))

            # Update student_profile table
            conn.execute('''UPDATE student_profile
                SET cgpa = ?, skills = ?, achievements = ?, resume_link = ?, semester = ?
                WHERE user_id = ?''',
                (cgpa, skills, achievements, resume_link, semester, user_id))

            conn.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('student_profile', user_id=user_id))

        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user or not profile:
            flash('Student not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('student/edit_profile.html', user=user, profile=profile)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit student profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('student_profile', user_id=user_id))
    finally:
        if conn:
            conn.close()

@app.route('/alumni/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_alumni_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            company_name = request.form.get('company_name', '').strip()
            designation = request.form.get('designation', '').strip()
            work_location = request.form.get('work_location', '').strip()
            experience_years = request.form.get('experience_years', '')
            linkedin_url = request.form.get('linkedin_url', '').strip()
            achievements = request.form.get('achievements', '').strip()
            bio = request.form.get('bio', '').strip()

            # Client-side validation already happens, so only save if data is valid
            # This is a backup validation
            if not name or not phone:
                # Don't redirect - keep form intact by re-rendering
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
                flash('Name and Phone are required!', 'warning')
                return render_template('alumni/edit_profile.html', user=user, profile=profile)

            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"alumni_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"

            if profile_pic:
                conn.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?',
                            (name, phone, user_id))

            conn.execute('''UPDATE alumni_profile
                SET company_name = ?, designation = ?, work_location = ?,
                    experience_years = ?, linkedin_url = ?, achievements = ?, bio = ?
                WHERE user_id = ?''',
                (company_name, designation, work_location, experience_years,
                 linkedin_url, achievements, bio, user_id))

            conn.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('alumni_profile', user_id=user_id))

        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('home'))

        profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()

        # If profile doesn't exist, create it
        if not profile:
            try:
                conn.execute('''INSERT INTO alumni_profile
                    (user_id, enrollment_no, department, degree, pass_year, company_name, designation,
                     work_location, experience_years, linkedin_url, achievements, bio)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (user_id, '', '', '', '', '', '', '', '', '', '', ''))
                conn.commit()
                profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()
            except Exception as e:
                print(f"Error creating alumni profile: {e}")
                flash('Error loading profile!', 'danger')
                return redirect(url_for('home'))

        return render_template('alumni/edit_profile.html', user=user, profile=profile)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit alumni profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('alumni_profile', user_id=user_id))
    finally:
        if conn:
            conn.close()

@app.route('/faculty/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_faculty_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()
            specialization = request.form.get('specialization', '').strip()
            experience_years = request.form.get('experience_years', '')
            office_location = request.form.get('office_location', '').strip()
            office_hours = request.form.get('office_hours', '').strip()
            bio = request.form.get('bio', '').strip()

            # Client-side validation already happens, so only save if data is valid
            # This is a backup validation
            if not name or not phone:
                # Don't redirect - keep form intact by re-rendering
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()
                flash('Name and Phone are required!', 'warning')
                return render_template('faculty/edit_profile.html', user=user, profile=profile)

            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"faculty_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"

            if profile_pic:
                conn.execute('UPDATE users SET name = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?',
                            (name, phone, user_id))

            conn.execute('''UPDATE faculty_profile
                SET specialization = ?, experience_years = ?, office_location = ?,
                    office_hours = ?, bio = ?
                WHERE user_id = ?''',
                (specialization, experience_years, office_location, office_hours, bio, user_id))

            conn.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('faculty_profile', user_id=user_id))

        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM faculty_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user or not profile:
            flash('Faculty not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('faculty/edit_profile.html', user=user, profile=profile)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit faculty profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('faculty_profile', user_id=user_id))
    finally:
        if conn:
            conn.close()

@app.route('/admin/profile/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_admin_profile(user_id):
    if current_user.id != user_id and current_user.role != 'admin':
        flash('You cannot edit this profile!', 'danger')
        return redirect(url_for('home'))

    if current_user.role != 'admin':
        flash('Only admins can edit admin profiles!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()

        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            phone = request.form.get('phone', '').strip()

            # Validation
            if not name or not email or not phone:
                user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()
                flash('Name, Email, and Phone are required!', 'warning')
                return render_template('admin/edit_admin_profile.html', user=user)

            # Handle profile photo upload
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"admin_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"

            # Update users table
            if profile_pic:
                conn.execute('UPDATE users SET name = ?, email = ?, phone = ?, profile_pic = ? WHERE id = ?',
                            (name, email, phone, profile_pic, user_id))
            else:
                conn.execute('UPDATE users SET name = ?, email = ?, phone = ? WHERE id = ?',
                            (name, email, phone, user_id))

            conn.commit()
            flash('Admin profile updated successfully!', 'success')
            return redirect(url_for('admin_profile', user_id=user_id))

        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user or user['role'] != 'admin':
            flash('Admin not found!', 'danger')
            return redirect(url_for('home'))

        return render_template('admin/edit_admin_profile.html', user=user)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Edit admin profile error: {e}")
        flash(f'Error updating profile: {str(e)}', 'danger')
        return redirect(url_for('admin_profile', user_id=user_id))
    finally:
        if conn:
            conn.close()

# --- FORGOT PASSWORD ROUTES ---

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        conn = None
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE email = ?', (email,)).fetchone()
            
            if user:
                # Generate Secure OTP
                otp = ''.join(secrets.choice(string.digits) for _ in range(6))
                
                # Store OTP
                conn.execute('INSERT INTO password_resets (email, otp) VALUES (?, ?)', (email, otp))
                conn.commit()
                
                # Email HTML
                html_content = f'''
                <!DOCTYPE html>
                <html>
                <body style="margin: 0; padding: 0; background-color: #f8fafc; font-family: Arial, sans-serif;">
                    <div style="max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 24px; overflow: hidden; box-shadow: 0 20px 40px rgba(0,0,0,0.05);">
                        
                        <!-- Header -->
                        <div style="background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%); padding: 40px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 28px; font-weight: 700;">Alumni Hub</h1>
                            <p style="color: rgba(255,255,255,0.7); margin: 10px 0 0 0; font-size: 14px;">Connecting Generations</p>
                        </div>

                        <!-- Body -->
                        <div style="padding: 40px;">
                            <h2 style="color: #1e293b; font-size: 22px; font-weight: 700; margin-top: 0; text-align: center;">🔐 Password Reset Request</h2>
                            
                            <p style="color: #64748b; line-height: 1.8; font-size: 16px; text-align: center; margin-bottom: 30px;">
                                We received a request to reset the password for your Alumni Hub account.<br>
                                Use the One-Time Password (OTP) below to proceed.
                            </p>

                            <div style="background: #f8fafc; border: 2px dashed #cbd5e1; border-radius: 16px; padding: 25px; text-align: center; margin-bottom: 30px;">
                                <span style="font-size: 36px; font-weight: 800; color: #4f46e5; letter-spacing: 8px; display: block; font-family: 'Courier New', monospace;">{otp}</span>
                                <span style="display: block; font-size: 12px; color: #94a3b8; margin-top: 10px;">VALID FOR 10 MINUTES</span>
                            </div>

                            <p style="color: #94a3b8; font-size: 14px; text-align: center;">
                                If you didn't request this, please ignore. Your password will remain unchanged.
                            </p>
                        </div>

                        <!-- Footer -->
                        <div style="background: #f1f5f9; padding: 20px; text-align: center; border-top: 1px solid #e2e8f0;">
                            <p style="color: #64748b; font-size: 12px; margin: 0;">&copy; 2026 Alumni Hub. All rights reserved.</p>
                        </div>
                    </div>
                </body>
                </html>
                '''
                
                # Send email
                email_sent, msg_text = send_email(email, '🔐 Reset Your Password - Alumni Hub', html_content)
                
                if email_sent:
                    flash('✓ OTP sent to your email!', 'success')
                    return redirect(url_for('verify_reset_otp', email=email))
                else:
                    logger.warning(f'Password reset email failed for {email}: {msg_text}. OTP: {otp}')
                    flash('⚠ Could not send OTP email. Please try again or contact admin.', 'warning')
                    return redirect(url_for('verify_reset_otp', email=email))
            else:
                flash('Email not found!', 'danger')
        except Exception as e:
            print(f"Forgot password error: {e}")
            flash(f'Error: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()
                
    return render_template('auth/forgot_password.html')


@app.route('/verify-reset-otp', methods=['GET', 'POST'])
def verify_reset_otp():
    email = request.args.get('email', '')
    if request.method == 'POST':
        email = request.form.get('email', '')
        otp = request.form.get('otp', '')
        
        conn = None
        try:
            conn = get_db_connection()
            # Check latest OTP for this email
            record = conn.execute('SELECT * FROM password_resets WHERE email = ? ORDER BY created_at DESC LIMIT 1', (email,)).fetchone()
            
            if record and record['otp'] == otp:
                # Check expiry (10 mins)
                otp_time = datetime.strptime(record['created_at'], '%Y-%m-%d %H:%M:%S')
                if (datetime.utcnow() - otp_time).total_seconds() > 600:
                    flash('OTP has expired! Please request a new one.', 'danger')
                    return redirect(url_for('forgot_password'))

                # Valid OTP - Single use enforcement: delete the record
                conn.execute('DELETE FROM password_resets WHERE id = ?', (record['id'],))
                conn.commit()
                
                session['reset_email'] = email
                flash('OTP Verified! Set your new password.', 'success')
                return redirect(url_for('reset_password_final'))
            else:
                flash('Invalid OTP!', 'danger')
        finally:
            if conn:
                conn.close()
                
    return render_template('auth/verify_otp.html', email=email, action_url='/verify-reset-otp')

@app.route('/reset-password-final', methods=['GET', 'POST'])
def reset_password_final():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))
        
    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        if password != confirm_password:
            flash('Passwords do not match!', 'warning')
            return render_template('auth/reset_password_final.html')

        # Enforce password strength (same as registration)
        pw_valid, pw_msg = validate_password(password)
        if not pw_valid:
            flash(pw_msg, 'warning')
            return render_template('auth/reset_password_final.html')
            
        conn = None
        try:
            conn = get_db_connection()
            email = session['reset_email']
            password_hash = generate_password_hash(password)
            
            conn.execute('UPDATE users SET password = ? WHERE email = ?', (password_hash, email))
            conn.commit()
            
            session.pop('reset_email', None)
            flash('Password reset successful! Please login.', 'success')
            return redirect(url_for('login'))
        finally:
            if conn:
                conn.close()
                
    return render_template('auth/reset_password_final.html')

# --- PASSWORD CHANGE ROUTES ---

@app.route('/change-password', methods=['GET', 'POST'])
@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password', '')
        new_password = request.form.get('new_password', '')
        confirm_password = request.form.get('confirm_password', '')

        if not all([old_password, new_password, confirm_password]):
            flash('All fields are required!', 'warning')
            return render_template('auth/change_password.html')

        if new_password != confirm_password:
            flash('New passwords do not match!', 'warning')
            return render_template('auth/change_password.html')

        pw_valid, pw_msg = validate_password(new_password)
        if not pw_valid:
            flash(pw_msg, 'warning')
            return render_template('auth/change_password.html')

        conn = None
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT password FROM users WHERE id = ?', (current_user.id,)).fetchone()

            if not check_password_hash(user['password'], old_password):
                flash('Old password is incorrect!', 'danger')
                return render_template('auth/change_password.html')

            new_password_hash = generate_password_hash(new_password)
            conn.execute('UPDATE users SET password = ? WHERE id = ?',
                        (new_password_hash, current_user.id))
            conn.commit()

            flash('Password changed successfully!', 'success')
            return redirect(url_for('profile'))

        except Exception as e:
            if conn:
                conn.rollback()
            flash(f'Error changing password: {str(e)}', 'danger')
        finally:
            if conn:
                conn.close()

    return render_template('auth/change_password.html')

# Add new routes for comprehensive profile features

# --- PROFILE COMPLETION & ENHANCEMENT ---

@app.route('/profile/complete/<int:user_id>', methods=['GET', 'POST'])
@login_required
def complete_profile(user_id):
    """Complete initial profile setup"""
    if current_user.id != user_id:
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if request.method == 'POST':
            # Handle profile photo
            profile_pic = None
            if 'profile_pic' in request.files:
                file = request.files['profile_pic']
                if file and file.filename and allowed_file(file.filename):
                    filename = secure_filename(f"{current_user.role}_{user_id}_{datetime.now().timestamp()}.{file.filename.rsplit('.', 1)[1].lower()}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                    profile_pic = f"/static/uploads/{filename}"
                    conn.execute('UPDATE users SET profile_pic = ? WHERE id = ?', (profile_pic, user_id))

            # Update common fields
            name = request.form.get('name', '').strip()
            phone = request.form.get('phone', '').strip()

            if name and phone:
                conn.execute('UPDATE users SET name = ?, phone = ? WHERE id = ?', (name, phone, user_id))

            conn.commit()
            flash('Profile completed successfully!', 'success')

            if current_user.role == 'student':
                return redirect(url_for('student_profile', user_id=user_id))
            elif current_user.role == 'alumni':
                return redirect(url_for('alumni_profile', user_id=user_id))
            elif current_user.role == 'faculty':
                return redirect(url_for('faculty_profile', user_id=user_id))

        role = user['role']
        return render_template('complete_profile.html', user=user, role=role)

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('profile'))
    finally:
        if conn:
            conn.close()

# --- ADMIN FEATURES ---

@app.route('/admin/verify-user/<int:user_id>/<action>')
@login_required
def verify_user(user_id, action):
    """Admin: Verify/Block users"""
    if current_user.role != 'admin':
        flash('Unauthorized!', 'danger')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()

        if action == 'approve':
            conn.execute('UPDATE users SET is_approved = 1 WHERE id = ?', (user_id,))
            flash('User verified successfully!', 'success')
        elif action == 'block':
            conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
            flash('User blocked/removed!', 'warning')

        conn.commit()
        return redirect(url_for('admin_view_users', role='student'))

    except Exception as e:
        if conn:
            conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/analytics')
@login_required
def admin_analytics():
    """Admin: View analytics and reports"""
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()

        # Gather statistics
        stats = {
            'total_users': conn.execute("SELECT COUNT(*) FROM users").fetchone()[0],
            'students': conn.execute("SELECT COUNT(*) FROM users WHERE role='student'").fetchone()[0],
            'alumni': conn.execute("SELECT COUNT(*) FROM users WHERE role='alumni'").fetchone()[0],
            'faculty': conn.execute("SELECT COUNT(*) FROM users WHERE role='faculty'").fetchone()[0],
            'admin': conn.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0],
            'meet_registrations': conn.execute("SELECT COUNT(*) FROM alumni_meet_registration").fetchone()[0],
        }

        return render_template('admin/admin_analytics.html', stats=stats)

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard_admin'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/registrations')
@login_required
def admin_registrations():
    """Admin: View registration logs"""
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get filter and search parameters
        role_filter = request.args.get('role_filter', '')
        search_query = request.args.get('search', '')

        # Build query with filters
        query = 'SELECT * FROM registration_log WHERE 1=1'
        params = []

        if role_filter:
            query += ' AND role = ?'
            params.append(role_filter)

        if search_query:
            query += ' AND (name LIKE ? OR email LIKE ?)'
            search_term = f'%{search_query}%'
            params.extend([search_term, search_term])

        query += ' ORDER BY registered_at DESC'

        registrations = c.execute(query, params).fetchall()

        # Get statistics
        stats = {
            'students': c.execute("SELECT COUNT(*) FROM registration_log WHERE role='student'").fetchone()[0],
            'alumni': c.execute("SELECT COUNT(*) FROM registration_log WHERE role='alumni'").fetchone()[0],
            'faculty': c.execute("SELECT COUNT(*) FROM registration_log WHERE role='faculty'").fetchone()[0],
            'total': c.execute("SELECT COUNT(*) FROM registration_log").fetchone()[0],
        }

        return render_template('admin/admin_registrations.html',
                             registrations=registrations,
                             stats=stats,
                             current_filter=role_filter,
                             search_query=search_query)

    except Exception as e:
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('dashboard_admin'))
    finally:
        if conn:
            conn.close()

@app.route('/admin/export/registrations')
@login_required
def admin_export_registrations():
    """Download all registration logs as a professional CSV community matrix"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized access to encrypted data'}), 403

    import csv
    from io import StringIO
    from flask import make_response

    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor()
        
        # Fetch all registration records
        c.execute('SELECT * FROM registration_log ORDER BY registered_at DESC')
        rows = c.fetchall()

        # Prepare CSV Buffer
        output = StringIO()
        writer = csv.writer(output)

        # Header Definition
        writer.writerow([
            'Record ID', 'Full Name', 'Email Address', 'Primary Phone', 
            'System Classification', 'Core Department', 'Academic Degree', 
            'Temporal Stamp (Registration)'
        ])

        # Data Row Mapping
        for row in rows:
            writer.writerow([
                row['id'],
                row['name'],
                row['email'],
                row['phone'],
                row['role'].upper() if row['role'] else 'N/A',
                row['department'] or 'General',
                row['degree'] or 'N/A',
                row['registered_at']
            ])

        csv_data = output.getvalue()
        response = make_response(csv_data)
        
        # Set headers for professional download
        filename = f"community_matrix_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        
        return response

    except Exception as e:
        print(f"Export Error: {e}")
        flash(f"System Error during matrix orchestration: {str(e)}", "danger")
        return redirect(url_for('admin_registrations'))
    finally:
        if conn:
            conn.close()

@app.route('/api/download-csv/<role>')
@login_required
def download_csv(role):
    """Download user data as CSV by role"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    import csv
    from io import StringIO
    from flask import make_response

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Prepare CSV
        output = StringIO()
        writer = csv.writer(output)

        if role.lower() == 'student':
            # Student data with profiles
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role,
                       s.enrollment_no, s.semester, s.cgpa, s.skills, s.department
                FROM users u
                LEFT JOIN student_profile s ON u.id = s.user_id
                WHERE u.role = 'student'
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role',
                           'Enrollment No', 'Semester', 'CGPA', 'Skills', 'Department'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'], row['phone'],
                    row['role'], row['enrollment_no'] or '', row['semester'] or '',
                    row['cgpa'] or '', row['skills'] or '', row['department'] or ''
                ])

        elif role.lower() == 'alumni':
            # Alumni data with profiles
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role,
                       a.enrollment_no, a.degree, a.pass_year, a.company_name,
                       a.designation, a.experience_years, a.department
                FROM users u
                LEFT JOIN alumni_profile a ON u.id = a.user_id
                WHERE u.role = 'alumni'
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role',
                           'Enrollment No', 'Degree', 'Pass Year', 'Company',
                           'Designation', 'Experience (Years)', 'Department'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'], row['phone'],
                    row['role'], row['enrollment_no'] or '', row['degree'] or '',
                    row['pass_year'] or '', row['company_name'] or '',
                    row['designation'] or '', row['experience_years'] or '',
                    row['department'] or ''
                ])

        elif role.lower() == 'faculty':
            # Faculty data with profiles
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role,
                       f.employee_id, f.designation, f.specialization, f.experience_years,
                       f.office_hours, f.department
                FROM users u
                LEFT JOIN faculty_profile f ON u.id = f.user_id
                WHERE u.role = 'faculty'
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role',
                           'Employee ID', 'Designation', 'Specialization',
                           'Experience (Years)', 'Office Hours', 'Department'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'], row['phone'],
                    row['role'], row['employee_id'] or '', row['designation'] or '',
                    row['specialization'] or '', row['experience_years'] or '',
                    row['office_hours'] or '', row['department'] or ''
                ])

        elif role.lower() == 'all':
            # All users combined
            c.execute('''
                SELECT u.id, u.name, u.email, u.phone, u.role
                FROM users u
                ORDER BY u.id DESC
            ''')

            writer.writerow(['ID', 'Name', 'Email', 'Phone', 'Role'])

            for row in c.fetchall():
                writer.writerow([
                    row['id'], row['name'], row['email'],
                    row['phone'], row['role']
                ])

        else:
            return jsonify({'error': 'Invalid role'}), 400

        conn.close()

        # Get CSV content
        csv_data = output.getvalue()

        # Create response with proper headers
        response = make_response(csv_data)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'{role.upper()}_Users_{timestamp}.csv'

        response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
        response.headers['Content-Type'] = 'text/csv; charset=utf-8'
        response.headers['Content-Length'] = len(csv_data)
        response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response.headers['Pragma'] = 'no-cache'
        response.headers['Expires'] = '0'

        return response, 200

    except Exception as e:
        print(f"Error generating CSV: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- DATABASE DOWNLOAD ROUTES ---

@app.route('/api/download-db/<db_type>')
@login_required
def download_database(db_type):
    """Download database files for student, alumni, faculty or complete database"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403

    import shutil
    import tempfile
    from flask import send_file

    try:
        db_types = {
            'college_pro': 'Complete College Database (All Users)',
            'student': 'Student Database Only',
            'alumni': 'Alumni Database Only',
            'faculty': 'Faculty Database Only'
        }

        if db_type not in db_types:
            return jsonify({'error': 'Invalid database type'}), 400

        # For now, we'll send the complete database file
        # In the future, you can create filtered databases
        db_file = DB_NAME  # alumni_hub.db

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # On Turso there is no local .db file to copy, so build a SQL dump
        # from the live connection instead.
        if is_turso():
            temp_fd, temp_path = tempfile.mkstemp(suffix='.sql')
            os.close(temp_fd)
            try:
                dump_to_sql(temp_path)
            except Exception as dump_error:
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                app.logger.error(f'Turso SQL dump failed: {dump_error}')
                return jsonify({'error': 'Could not export database'}), 500

            return send_file(
                temp_path,
                mimetype='application/sql',
                as_attachment=True,
                download_name=f'{db_type.upper()}_Database_{timestamp}.sql'
            )

        if not os.path.exists(db_file):
            return jsonify({'error': 'Database file not found'}), 404

        # Create a temporary copy
        temp_fd, temp_path = tempfile.mkstemp(suffix='.db')
        os.close(temp_fd)

        try:
            shutil.copy2(db_file, temp_path)

            return send_file(
                temp_path,
                mimetype='application/x-sqlite3',
                as_attachment=True,
                download_name=f'{db_type.upper()}_Database_{timestamp}.db'
            )
        except Exception as copy_error:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise copy_error

    except Exception as e:
        print(f"Error downloading database: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# --- USER DELETION ROUTES ---

@app.route('/api/delete-user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user and all their data from the database"""
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized: Only admins can delete users'}), 403

    try:
        conn = get_db_connection()
        c = conn.cursor()

        # Get user details first for logging
        user = c.execute('SELECT * FROM users WHERE id = ?', (user_id,)).fetchone()

        if not user:
            conn.close()
            return jsonify({'error': 'User not found'}), 404

        # PROTECTION: Prevent deletion of super admin account
        if user['email'] == 'admindbit195@college.edu':
            conn.close()
            return jsonify({'error': 'Cannot delete the Super Admin account. This account is protected.'}), 403

        user_role = user['role']
        user_name = user['name']
        user_email = user['email']

        print(f"[DELETE DEBUG] Starting deletion for User ID: {user_id}, Role: {user_role}")

        # Delete from profile tables first (cascading)
        if user_role == 'student':
            result = c.execute('DELETE FROM student_profile WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] student_profile rows deleted: {result.rowcount}")
        elif user_role == 'alumni':
            result = c.execute('DELETE FROM alumni_profile WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] alumni_profile rows deleted: {result.rowcount}")
        elif user_role == 'faculty':
            result = c.execute('DELETE FROM faculty_profile WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] faculty_profile rows deleted: {result.rowcount}")

        # Delete from alumni_meet_registration (can be deleted for any user)
        result_amr = c.execute('DELETE FROM alumni_meet_registration WHERE user_id = ?', (user_id,))
        print(f"[DELETE DEBUG] alumni_meet_registration rows deleted: {result_amr.rowcount}")

        # Delete from registration_log (can be deleted for any user)
        try:
            result_reglog = c.execute('DELETE FROM registration_log WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] registration_log rows deleted: {result_reglog.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] registration_log table error: {e}")

        # Delete from connection tables
        result1 = c.execute('DELETE FROM connection_requests WHERE sender_id = ? OR receiver_id = ?', (user_id, user_id))
        print(f"[DELETE DEBUG] connection_requests rows deleted: {result1.rowcount}")

        try:
            result2 = c.execute('DELETE FROM connections WHERE user_id_1 = ? OR user_id_2 = ?', (user_id, user_id))
            print(f"[DELETE DEBUG] connections rows deleted: {result2.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] connections table error (may not exist or different schema): {e}")


        # Delete from other related tables (if they exist)
        try:
            result3 = c.execute('DELETE FROM posts WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] posts rows deleted: {result3.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] posts table error (may not exist): {e}")

        try:
            result4 = c.execute('DELETE FROM comments WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] comments rows deleted: {result4.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] comments table error (may not exist): {e}")

        try:
            result5 = c.execute('DELETE FROM likes WHERE user_id = ?', (user_id,))
            print(f"[DELETE DEBUG] likes rows deleted: {result5.rowcount}")
        except Exception as e:
            print(f"[DELETE DEBUG] likes table error (may not exist): {e}")

        # Finally, delete the user record
        result6 = c.execute('DELETE FROM users WHERE id = ?', (user_id,))
        print(f"[DELETE DEBUG] users rows deleted: {result6.rowcount}")

        conn.commit()
        conn.close()

        # Log the deletion
        print(f"[ADMIN DELETE] ✅ Successfully deleted User ID: {user_id}, Name: {user_name}, Email: {user_email}, Role: {user_role}")

        return jsonify({
            'success': True,
            'message': f'User "{user_name}" ({user_email}) has been permanently deleted from the database',
            'user_id': user_id,
            'user_name': user_name
        }), 200

    except Exception as e:
        print(f"[ADMIN DELETE] ❌ Error deleting user: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Error deleting user: {str(e)}'}), 500

# --- ADMIN JOB MANAGEMENT ---

@app.route('/admin/jobs')
@login_required
def admin_jobs():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    
    conn = None
    try:
        conn = get_db_connection()
        today = datetime.now().strftime('%Y-%m-%d')

        # Pending approval queue (jobs posted by alumni/faculty awaiting admin review)
        pending_jobs = conn.execute('''
            SELECT j.*, u.name as posted_by_name, u.role as poster_role
            FROM jobs j 
            LEFT JOIN users u ON j.posted_by = u.id 
            WHERE j.approval_status = 'pending'
            ORDER BY j.created_at DESC
        ''').fetchall()

        # All approved jobs
        jobs = conn.execute('''
            SELECT j.*, u.name as posted_by_name, u.role as poster_role
            FROM jobs j 
            LEFT JOIN users u ON j.posted_by = u.id 
            WHERE j.approval_status != 'pending' OR j.approval_status IS NULL
            ORDER BY j.created_at DESC
        ''').fetchall()
        
        total_jobs = conn.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        active_jobs = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE is_active = 1 AND approval_status = 'approved'"
        ).fetchone()[0]
        pending_count = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE approval_status = 'pending'"
        ).fetchone()[0]
        expired_jobs = conn.execute(
            "SELECT COUNT(*) FROM jobs WHERE deadline < ? AND deadline != '' AND deadline IS NOT NULL AND approval_status = 'approved'",
            (today,)
        ).fetchone()[0]
        
        stats = {
            'total': total_jobs,
            'active': active_jobs,
            'expired': expired_jobs,
            'pending': pending_count,
            'inactive': total_jobs - active_jobs
        }
        
        return render_template('admin/jobs.html', jobs=jobs, pending_jobs=pending_jobs, stats=stats)
    finally:
        if conn:
            conn.close()

@app.route('/admin/jobs/approve/<int:job_id>', methods=['POST'])
@login_required
def admin_approve_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = None
    try:
        conn = get_db_connection()
        conn.execute(
            "UPDATE jobs SET approval_status = 'approved', is_active = 1 WHERE id = ?",
            (job_id,)
        )
        conn.commit()
        # Notify the poster via SocketIO if online
        job = conn.execute('SELECT posted_by, title FROM jobs WHERE id = ?', (job_id,)).fetchone()
        if job:
            socketio.emit('job_approval_update', {
                'status': 'approved',
                'job_id': job_id,
                'job_title': job['title'],
            }, room=f"user_{job['posted_by']}")
        return jsonify({'success': True, 'message': 'Job approved and is now visible to students.'})
    except Exception as e:
        logger.error(f"Error approving job: {e}")
        return jsonify({'error': 'Failed to approve job'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/admin/jobs/reject/<int:job_id>', methods=['POST'])
@login_required
def admin_reject_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = None
    try:
        data = request.get_json(silent=True) or {}
        reason = data.get('reason', '')
        conn = get_db_connection()
        conn.execute(
            "UPDATE jobs SET approval_status = 'rejected', is_active = 0, rejection_reason = ? WHERE id = ?",
            (reason, job_id)
        )
        conn.commit()
        job = conn.execute('SELECT posted_by, title FROM jobs WHERE id = ?', (job_id,)).fetchone()
        if job:
            socketio.emit('job_approval_update', {
                'status': 'rejected',
                'job_id': job_id,
                'job_title': job['title'],
                'reason': reason,
            }, room=f"user_{job['posted_by']}")
        return jsonify({'success': True, 'message': 'Job rejected.'})
    except Exception as e:
        logger.error(f"Error rejecting job: {e}")
        return jsonify({'error': 'Failed to reject job'}), 500
    finally:
        if conn:
            conn.close()


@app.route('/api/admin/jobs/pending-count', methods=['GET'])
@login_required
def api_pending_jobs_count():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
    conn = None
    try:
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) FROM jobs WHERE approval_status = 'pending'").fetchone()[0]
        return jsonify({'count': count})
    except Exception as e:
        logger.error(f"Error fetching pending jobs count: {e}")
        return jsonify({'count': 0})
    finally:
        if conn:
            conn.close()


@app.route('/api/admin/jobs/toggle/<int:job_id>', methods=['POST'])
@login_required
def admin_toggle_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = None
    try:
        conn = get_db_connection()
        job = conn.execute('SELECT is_active FROM jobs WHERE id = ?', (job_id,)).fetchone()
        
        if not job:
            return jsonify({'error': 'Job not found'}), 404
            
        new_status = 1 if job['is_active'] == 0 else 0
        conn.execute('UPDATE jobs SET is_active = ? WHERE id = ?', (new_status, job_id))
        conn.commit()
        
        return jsonify({'success': True, 'new_status': new_status})
    finally:
        if conn:
            conn.close()

@app.route('/admin/jobs/add', methods=['GET', 'POST'])
@login_required
def admin_add_job():
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    if request.method == 'POST':
        # Basic Info
        title = request.form.get('title')
        company_name = request.form.get('company_name')
        company_website = request.form.get('company_website')
        description = request.form.get('description')
        
        # Location & Mode
        location_select = request.form.get('location_select')
        location_manual = request.form.get('location_manual')
        location = location_manual if location_select == 'Other' else location_select
        work_mode = request.form.get('work_mode')
        
        # Type & Eligibility
        employment_type = request.form.get('employment_type')
        eligible_branch = request.form.get('eligible_branch')
        eligible_batch = request.form.get('eligible_batch')
        qualification = request.form.get('qualification')
        min_cgpa = request.form.get('min_cgpa')
        experience_required = request.form.get('experience_required')
        
        # Skills
        skills_required = request.form.get('skills_required')
        skills_preferred = request.form.get('skills_preferred')
        
        # Salary
        salary = request.form.get('salary')
        ctc_range = request.form.get('ctc_range')
        perks = request.form.get('perks')
        
        # Dates
        deadline = request.form.get('deadline')
        joining_date = request.form.get('joining_date')
        
        # Apply & Hiring
        apply_method = request.form.get('apply_method')
        apply_link = request.form.get('apply_link')
        openings = request.form.get('openings', 0)
        selection_list = request.form.getlist('selection[]')
        selection_process = ", ".join(selection_list) if selection_list else ""
        
        # Intel
        category = request.form.get('category')
        target_role = request.form.get('target_role')
        skill_level = request.form.get('skill_level')
        
        if not title or not company_name:
            flash('Title and Company are required!', 'warning')
            return redirect(url_for('admin_add_job'))
            
        # Handle Logo Upload
        logo_path = None
        if 'company_logo' in request.files:
            file = request.files['company_logo']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    logo_path = os.path.join('static/uploads/company_logos', filename)
                    file.save(logo_path)
                    logo_path = '/' + logo_path.replace('\\', '/')
            
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO jobs (
                title, company, company_name, company_website, description, 
                location, work_mode, employment_type, eligible_branch, eligible_batch, 
                qualification, min_cgpa, experience_required, skills_required, skills_preferred, 
                salary, ctc_range, perks, deadline, joining_date, 
                apply_method, apply_link, openings, selection_process, category, 
                target_role, skill_level, posted_by, company_logo, job_status
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, company_name, company_name, company_website, description,
            location, work_mode, employment_type, eligible_branch, eligible_batch,
            qualification, min_cgpa, experience_required, skills_required, skills_preferred,
            salary, ctc_range, perks, deadline, joining_date,
            apply_method, apply_link, openings, selection_process, category,
            target_role, skill_level, current_user.id, logo_path, 'Open'
        ))
        conn.commit()
        conn.close()
        
        flash('Job added successfully!', 'success')
        return redirect(url_for('admin_jobs'))
        
    return render_template('admin/add_job.html')

@app.route('/admin/jobs/edit/<int:job_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    c = conn.cursor()
    job = c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,)).fetchone()
    
    if not job:
        conn.close()
        flash('Job not found!', 'danger')
        return redirect(url_for('admin_jobs'))
        
    if request.method == 'POST':
        # Field Extraction
        title = request.form.get('title')
        company_name = request.form.get('company_name')
        company_website = request.form.get('company_website')
        description = request.form.get('description')
        
        location_select = request.form.get('location_select')
        location_manual = request.form.get('location_manual')
        location = location_manual if location_select == 'Other' else location_select
        work_mode = request.form.get('work_mode')
        
        employment_type = request.form.get('employment_type')
        eligible_branch = request.form.get('eligible_branch')
        eligible_batch = request.form.get('eligible_batch')
        qualification = request.form.get('qualification')
        min_cgpa = request.form.get('min_cgpa')
        experience_required = request.form.get('experience_required')
        
        skills_required = request.form.get('skills_required')
        skills_preferred = request.form.get('skills_preferred')
        
        salary = request.form.get('salary')
        ctc_range = request.form.get('ctc_range')
        perks = request.form.get('perks')
        
        deadline = request.form.get('deadline')
        joining_date = request.form.get('joining_date')
        
        apply_method = request.form.get('apply_method')
        apply_link = request.form.get('apply_link')
        openings = request.form.get('openings', job['openings'])
        selection_list = request.form.getlist('selection[]')
        selection_process = ", ".join(selection_list) if selection_list else job['selection_process']
        
        category = request.form.get('category')
        target_role = request.form.get('target_role')
        skill_level = request.form.get('skill_level')
        job_status = request.form.get('job_status', job['job_status'])

        logo_path = job['company_logo']
        if 'company_logo' in request.files:
            file = request.files['company_logo']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    logo_path = os.path.join('static/uploads/company_logos', filename)
                    file.save(logo_path)
                    logo_path = '/' + logo_path.replace('\\', '/')

        c.execute('''
            UPDATE jobs SET 
                title=?, company=?, company_name=?, company_website=?, description=?,
                location=?, work_mode=?, employment_type=?, eligible_branch=?, eligible_batch=?,
                qualification=?, min_cgpa=?, experience_required=?, skills_required=?, skills_preferred=?,
                salary=?, ctc_range=?, perks=?, deadline=?, joining_date=?,
                apply_method=?, apply_link=?, openings=?, selection_process=?, category=?,
                target_role=?, skill_level=?, company_logo=?, job_status=?
            WHERE id=?
        ''', (
            title, company_name, company_name, company_website, description,
            location, work_mode, employment_type, eligible_branch, eligible_batch,
            qualification, min_cgpa, experience_required, skills_required, skills_preferred,
            salary, ctc_range, perks, deadline, joining_date,
            apply_method, apply_link, openings, selection_process, category,
            target_role, skill_level, logo_path, job_status, job_id
        ))
        conn.commit()
        conn.close()
        flash('Job updated successfully!', 'success')
        return redirect(url_for('admin_jobs'))
        
    conn.close()
    return render_template('admin/edit_job.html', job=job)

@app.route('/admin/whatsapp-broadcast', methods=['GET', 'POST'])
@login_required
def admin_whatsapp_broadcast():
    """Send WhatsApp notifications to users based on role"""
    if current_user.role != 'admin':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('home'))

    users = []
    selected_role = 'all'
    message = ''
    auto_start = False

    if request.method == 'POST':
        action = request.form.get('action', 'generate')
        selected_role = request.form.get('role', 'all')
        message = request.form.get('message', '').strip()
        
        if action == 'auto_send':
            auto_start = True

        if not message:
            flash('Please enter a message to broadcast.', 'warning')
        else:
            conn = get_db_connection()
            # Exclude admins from the broadcast list
            query = "SELECT name, role, phone FROM users WHERE is_verified = 1 AND role != 'admin'"
            params = []

            if selected_role != 'all':
                query += " AND role = ?"
                params.append(selected_role)

            rows = conn.execute(query, params).fetchall()
            conn.close()

            encoded_message = quote(message)
            for row in rows:
                phone = row['phone']
                clean_phone = ''.join(filter(str.isdigit, str(phone or '')))
                
                # Normalize preview links too
                if len(clean_phone) == 10:
                    clean_phone = '91' + clean_phone
                elif len(clean_phone) > 10 and not clean_phone.startswith('91'):
                    clean_phone = clean_phone[-10:]
                    clean_phone = '91' + clean_phone
                
                whatsapp_url = f"https://wa.me/{clean_phone}?text={encoded_message}"
                users.append({
                    'name': row['name'],
                    'role': row['role'],
                    'phone': row['phone'],
                    'whatsapp_url': whatsapp_url
                })

            if not users:
                flash(f'No verified users found for role: {selected_role}', 'info')

    return render_template('admin/whatsapp_broadcast.html', users=users, selected_role=selected_role, message=message, auto_start=auto_start)

@app.route('/admin/whatsapp-send-api', methods=['POST'])
@login_required
def admin_whatsapp_send_api():
    """API endpoint to send a WhatsApp message automatically using pywhatkit"""
    import pywhatkit as kit # Lazy load to speed up app startup
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
    
    data = request.json
    phone = data.get('phone')
    message = data.get('message')
    
    if not phone or not message:
        return jsonify({'success': False, 'error': 'Missing phone or message'}), 400
    
    try:
        # Sanitize phone number (remove non-digits)
        clean_phone = ''.join(filter(str.isdigit, str(phone)))
        
        # Validation: Check if phone number is logically correct (min 10 digits)
        if len(clean_phone) < 10:
            return jsonify({'success': False, 'error': 'Invalid Phone Number (Short)'}), 400
            
        # Ensure country code (default to +91 for India if missing)
        if len(clean_phone) == 10:
            clean_phone = '91' + clean_phone
        if not clean_phone.startswith('91') and len(clean_phone) > 10:
            # Handle cases where user might have entered 0 prefix or other variations
            clean_phone = clean_phone[-10:] # Take last 10
            clean_phone = '91' + clean_phone
            
        # Add the + prefix required by pywhatkit
        clean_phone = '+' + clean_phone
            
        # Final check: Must start with + and have at least 12 characters (+, 91, and 9 digits min)
        if len(clean_phone) < 12:
            print(f"WhatsApp Error: Invalid formatted number: {clean_phone}")
            return jsonify({'success': False, 'error': f'Invalid Phone Format: {clean_phone}'}), 400

        print(f"WhatsApp API: Sending to {clean_phone}")
        
        # pywhatkit.sendwhatmsg_instantly opens a tab, types the message, and sends it.
        kit.sendwhatmsg_instantly(
            phone_no=clean_phone,
            message=message,
            wait_time=15,
            tab_close=True,
            close_time=3
        )
        
        return jsonify({'success': True, 'message': 'Message sequence initiated'})
    except Exception as e:
        print(f"WhatsApp API Error: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/admin/jobs/delete/<int:job_id>', methods=['POST'])
@login_required
def admin_delete_job(job_id):
    if current_user.role != 'admin':
        return jsonify({'error': 'Unauthorized'}), 403
        
    conn = None
    try:
        conn = get_db_connection()
        conn.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
        conn.commit()
        
        flash('Job deleted successfully!', 'success')
        return redirect(url_for('admin_jobs'))
    finally:
        if conn:
            conn.close()

# --- NETWORKING & CONNECTIONS ---

@app.route('/network/search', methods=['GET', 'POST'])
@login_required
def search_network():
    """Search and filter users"""
    conn = None
    try:
        conn = get_db_connection()
        results = []

        if request.method == 'POST':
            search_term = request.form.get('search', '').strip()
            filter_role = request.form.get('role', '')

            if search_term:
                if filter_role:
                    results = conn.execute(
                        "SELECT * FROM users WHERE (name LIKE ? OR email LIKE ?) AND role = ? LIMIT 50",
                        (f"%{search_term}%", f"%{search_term}%", filter_role)
                    ).fetchall()
                else:
                    results = conn.execute(
                        "SELECT * FROM users WHERE name LIKE ? OR email LIKE ? LIMIT 50",
                        (f"%{search_term}%", f"%{search_term}%")
                    ).fetchall()

        return render_template('search_network.html', results=results)

    finally:
        if conn:
            conn.close()

# --- SEO ROUTES ---

@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt from static folder"""
    return send_from_directory(app.static_folder, 'robots.txt')

@app.route('/sitemap.xml')
def sitemap_xml():
    """Serve sitemap.xml from static folder"""
    return send_from_directory(app.static_folder, 'sitemap.xml')

# --- NOTIFICATIONS & UPDATES ---

# Removed - notifications route moved to student-specific section


# --- STUDENT TO ALUMNI UPGRADE ---

@app.route('/student/upgrade-to-alumni', methods=['GET', 'POST'])
@login_required
def upgrade_to_alumni():
    """Upgrade student role to alumni"""
    if current_user.role != 'student':
        flash('Only students can upgrade to alumni!', 'warning')
        return redirect(url_for('home'))

    conn = None
    try:
        conn = get_db_connection()
        if request.method == 'POST':
            # Get student profile
            student_profile = conn.execute(
                'SELECT * FROM student_profile WHERE user_id = ?',
                (current_user.id,)
            ).fetchone()

            if not student_profile:
                flash('Student profile not found!', 'danger')
                return redirect(url_for('dashboard_student'))

            # Get form data
            pass_year = request.form.get('pass_year', '')
            company_name = request.form.get('company_name', '')
            designation = request.form.get('designation', '')

            if not pass_year:
                flash('Year of passing is required!', 'warning')
                return render_template('upgrade_to_alumni.html', profile=student_profile)

            # Update user role
            conn.execute('UPDATE users SET role = ? WHERE id = ?', ('alumni', current_user.id))

            # Create alumni profile
            conn.execute('''INSERT INTO alumni_profile
                (user_id, enrollment_no, department, degree, pass_year, company_name, designation)
                VALUES (?, ?, ?, ?, ?, ?, ?)''',
                (current_user.id, student_profile['enrollment_no'],
                 student_profile['department'], student_profile['degree'],
                 pass_year, company_name, designation))

            conn.commit()

            flash('Successfully upgraded to Alumni! Your role has been changed.', 'success')
            return redirect(url_for('alumni_profile', user_id=current_user.id))

        # GET request - fetch student profile
        student_profile = conn.execute(
            'SELECT * FROM student_profile WHERE user_id = ?',
            (current_user.id,)
        ).fetchone()

        if not student_profile:
            flash('Student profile not found!', 'danger')
            return redirect(url_for('dashboard_student'))

        return render_template('upgrade_to_alumni.html', profile=student_profile)

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Upgrade to alumni error: {e}")
        flash(f'Error upgrading to alumni: {str(e)}', 'danger')
        return redirect(url_for('dashboard_student'))
    finally:
        if conn:
            conn.close()

@app.route('/upgrade')
@login_required
def upgrade():
    """Route to handle various upgrades based on role"""
    if current_user.role == 'student':
        return render_template('student/upgrade.html')
    elif current_user.role == 'alumni':
        conn = None
        try:
            conn = get_db_connection()
            profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (current_user.id,)).fetchone()
            return render_template('alumni/upgrade.html', profile=profile)
        finally:
            if conn:
                conn.close()
    else:
        return render_template('upgrade.html')



# --- API ROUTES FOR MODALS ---

@app.route('/api/faculty/students')
@login_required
def get_faculty_students():
    """Get all students for faculty dashboard"""
    if current_user.role != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = None
    try:
        conn = get_db_connection()

        # Get all students
        students = conn.execute('''
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   sp.enrollment_no, sp.department, sp.degree, sp.semester, sp.cgpa, sp.skills
            FROM users u
            LEFT JOIN student_profile sp ON u.id = sp.user_id
            WHERE u.role = 'student'
            ORDER BY u.name ASC
        ''').fetchall()

        total = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('student',)).fetchone()['count']

        return jsonify({
            'students': [dict(s) for s in students],
            'total_students': total
        })
    except Exception as e:
        print(f"Error getting students: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/faculty/alumni')
@login_required
def get_faculty_alumni():
    """Get all alumni for faculty dashboard"""
    if current_user.role != 'faculty':
        return jsonify({'error': 'Unauthorized'}), 403

    conn = None
    try:
        conn = get_db_connection()

        # Get all alumni
        alumni = conn.execute('''
            SELECT u.id, u.name, u.email, u.phone, u.profile_pic,
                   ap.department, ap.company_name, ap.designation, ap.work_location, ap.experience_years, ap.bio
            FROM users u
            LEFT JOIN alumni_profile ap ON u.id = ap.user_id
            WHERE u.role = 'alumni'
            ORDER BY u.name ASC
        ''').fetchall()

        total = conn.execute('SELECT COUNT(*) as count FROM users WHERE role = ?', ('alumni',)).fetchone()['count']

        return jsonify({
            'alumni': [dict(a) for a in alumni],
            'total_alumni': total
        })
    except Exception as e:
        print(f"Error getting alumni: {e}")
        return jsonify({'error': str(e)}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/alumni/<int:user_id>')
@login_required
def get_alumni_details(user_id):
    """Get alumni details for modal display"""
    if current_user.role not in ['admin', 'alumni', 'student', 'faculty']:
        return jsonify({'error': 'Unauthorized'}), 403

    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT id, name, email, profile_pic FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT * FROM alumni_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user or not profile:
            return jsonify({'error': 'Alumni not found'}), 404

        user_dict = dict(user)
        user_dict['profile_pic'] = normalize_profile_pic(user_dict['profile_pic'], user_dict['name'])

        return jsonify({
            'user': user_dict,
            'profile': dict(profile)
        })
    finally:
        if conn:
            conn.close()

@app.route('/api/student/<int:user_id>')
@login_required
def get_student_details(user_id):
    """Get student details for modal display"""
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT id, name, email, profile_pic FROM users WHERE id = ?', (user_id,)).fetchone()
        profile = conn.execute('SELECT department, degree, semester FROM student_profile WHERE user_id = ?', (user_id,)).fetchone()

        if not user or not profile:
            return jsonify({'error': 'Student not found'}), 404

        user_dict = dict(user)
        user_dict['profile_pic'] = normalize_profile_pic(user_dict['profile_pic'], user_dict['name'])

        return jsonify({
            'user': user_dict,
            'profile': dict(profile)
        })
    finally:
        if conn:
            conn.close()


# ===== UNIFIED CONNECTION REQUEST SYSTEM (Role-Agnostic) =====

@app.route('/api/connection-request/send', methods=['POST'])
@login_required
def send_connection_request():
    """Send a connection request from current user to any other user."""
    conn = None
    try:
        data = request.get_json()
        receiver_id = data.get('receiver_id')

        if not receiver_id or receiver_id == current_user.id:
            return jsonify({'error': 'Invalid recipient'}), 400

        conn = get_db_connection()
        c = conn.cursor()

        # Check if receiver exists
        receiver = conn.execute('SELECT * FROM users WHERE id = ?', (receiver_id,)).fetchone()
        if not receiver:
            return jsonify({'error': 'Recipient not found'}), 404

        # Check if already connected
        existing_connection = conn.execute('''
            SELECT 1 FROM connections
            WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        ''', (current_user.id, receiver_id, receiver_id, current_user.id)).fetchone()

        if existing_connection:
            return jsonify({'error': 'Already connected', 'status': 'connected'}), 400

        # Check if request already pending
        existing_request = conn.execute('''
            SELECT 1 FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (current_user.id, receiver_id)).fetchone()

        if existing_request:
            return jsonify({'error': 'Request already sent', 'status': 'pending'}), 400

        # Check for mutual request (auto-connect)
        mutual_request = conn.execute('''
            SELECT 1 FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (receiver_id, current_user.id)).fetchone()

        if mutual_request:
            conn.execute(
                '''
                UPDATE connection_requests
                SET status = ?, accepted_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                WHERE sender_id = ? AND receiver_id = ?
                ''',
                ('accepted', receiver_id, current_user.id)
            )
            conn.execute('INSERT INTO connections (user_id_1, user_id_2) VALUES (?, ?)',
                     (min(current_user.id, receiver_id), max(current_user.id, receiver_id)))
            conn.commit()

            try:
                send_connection_email(receiver['email'], receiver['name'], current_user.name, current_user.role, 'mutual')
            except Exception as e:
                logger.warning(f"Connection email error: {e}")

            return jsonify({'success': True, 'status': 'connected', 'message': 'Now connected!'}), 200

        # Create new request
        conn.execute('''
            INSERT INTO connection_requests (sender_id, receiver_id, status)
            VALUES (?, ?, 'pending')
        ''', (current_user.id, receiver_id))
        conn.commit()

        try:
            send_connection_email(receiver['email'], receiver['name'], current_user.name, current_user.role, 'request')
        except Exception as e:
            logger.warning(f"Connection email error: {e}")

        # Real-time: notify receiver on their dashboard
        socketio.emit('connection_request_received', {
            'sender_id': current_user.id,
            'sender_name': current_user.name,
            'sender_role': current_user.role,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }, room=f'user_{receiver_id}')

        # Real-time: notify admin monitor
        socketio.emit('admin_connection_activity', {
            'event': 'new_request',
            'sender_id': current_user.id,
            'sender_name': current_user.name,
            'sender_role': current_user.role,
            'receiver_id': receiver_id,
            'receiver_name': receiver['name'],
            'receiver_role': receiver['role'],
            'status': 'pending',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }, room='admin_monitor')

        return jsonify({'success': True, 'status': 'pending', 'message': 'Request sent'}), 200

    except Exception as e:
        logger.error(f"Error sending connection request: {e}")
        return jsonify({'error': 'Failed to send request'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/connection-request/accept/<int:sender_id>', methods=['POST'])
@login_required
def accept_connection_request(sender_id):
    """Accept a connection request"""
    conn = None
    try:
        conn = get_db_connection()

        sender = conn.execute('SELECT * FROM users WHERE id = ?', (sender_id,)).fetchone()

        conn.execute('''
            UPDATE connection_requests
            SET status = 'accepted', accepted_at = CURRENT_TIMESTAMP
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (sender_id, current_user.id))

        conn.execute('''
            INSERT OR IGNORE INTO connections (user_id_1, user_id_2)
            VALUES (?, ?)
        ''', (min(sender_id, current_user.id), max(sender_id, current_user.id)))

        conn.commit()

        try:
            if sender:
                send_connection_email(sender['email'], sender['name'], current_user.name, current_user.role, 'accepted')
        except Exception as e:
            logger.warning(f"Connection email error: {e}")

        # Real-time: notify the original sender that their request was accepted
        socketio.emit('connection_status_update', {
            'status': 'accepted',
            'by_user_id': current_user.id,
            'by_user_name': current_user.name,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }, room=f'user_{sender_id}')

        # Real-time: notify admin monitor
        socketio.emit('admin_connection_activity', {
            'event': 'accepted',
            'sender_id': sender_id,
            'sender_name': sender['name'] if sender else '',
            'receiver_id': current_user.id,
            'receiver_name': current_user.name,
            'status': 'accepted',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }, room='admin_monitor')

        return jsonify({'success': True, 'message': 'Request accepted', 'status': 'connected'}), 200

    except Exception as e:
        logger.error(f"Error accepting connection request: {e}")
        return jsonify({'error': 'Failed to accept request'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/connection-request/reject/<int:sender_id>', methods=['POST'])
@login_required
def reject_connection_request(sender_id):
    """Reject a connection request"""
    conn = None
    try:
        conn = get_db_connection()

        sender = conn.execute('SELECT * FROM users WHERE id = ?', (sender_id,)).fetchone()

        conn.execute('''
            UPDATE connection_requests
            SET status = 'rejected', accepted_at = NULL
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (sender_id, current_user.id))

        conn.commit()

        try:
            if sender:
                send_connection_email(sender['email'], sender['name'], current_user.name, current_user.role, 'rejected')
        except Exception as e:
            logger.warning(f"Connection email error: {e}")

        # Real-time: notify the original sender that their request was rejected
        socketio.emit('connection_status_update', {
            'status': 'rejected',
            'by_user_id': current_user.id,
            'by_user_name': current_user.name,
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }, room=f'user_{sender_id}')

        # Real-time: notify admin monitor
        socketio.emit('admin_connection_activity', {
            'event': 'rejected',
            'sender_id': sender_id,
            'sender_name': sender['name'] if sender else '',
            'receiver_id': current_user.id,
            'receiver_name': current_user.name,
            'status': 'rejected',
            'timestamp': datetime.utcnow().strftime('%Y-%m-%d %H:%M')
        }, room='admin_monitor')

        return jsonify({'success': True, 'message': 'Request rejected', 'status': 'none'}), 200

    except Exception as e:
        logger.error(f"Error rejecting connection request: {e}")
        return jsonify({'error': 'Failed to reject request'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/connection-request/status/<int:user_id>', methods=['GET'])
@login_required
def get_connection_status(user_id):
    """Get connection status between current user and another user"""
    conn = None
    try:
        conn = get_db_connection()

        connection = conn.execute('''
            SELECT 1 FROM connections
            WHERE (user_id_1 = ? AND user_id_2 = ?) OR (user_id_1 = ? AND user_id_2 = ?)
        ''', (current_user.id, user_id, user_id, current_user.id)).fetchone()

        if connection:
            return jsonify({'status': 'connected'}), 200

        sent_request = conn.execute('''
            SELECT 1 FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (current_user.id, user_id)).fetchone()

        if sent_request:
            return jsonify({'status': 'pending'}), 200

        received_request = conn.execute('''
            SELECT 1 FROM connection_requests
            WHERE sender_id = ? AND receiver_id = ? AND status = 'pending'
        ''', (user_id, current_user.id)).fetchone()

        if received_request:
            return jsonify({'status': 'received', 'sender_id': user_id}), 200

        return jsonify({'status': 'none'}), 200

    except Exception as e:
        logger.error(f"Error getting connection status: {e}")
        return jsonify({'error': 'Failed to get status'}), 500
    finally:
        if conn:
            conn.close()

@app.route('/api/connection-requests/pending', methods=['GET'])
@login_required
def get_pending_connection_requests():
    """Get all pending connection requests for current user"""
    conn = None
    try:
        conn = get_db_connection()

        requests_list = conn.execute('''
            SELECT cr.id, cr.sender_id, cr.receiver_id, cr.status, cr.created_at,
                   u.name, u.email, u.role, u.profile_pic
            FROM connection_requests cr
            JOIN users u ON cr.sender_id = u.id
            WHERE cr.receiver_id = ? AND cr.status = 'pending'
            ORDER BY cr.created_at DESC
        ''', (current_user.id,)).fetchall()

        return jsonify({
            'requests': [dict(req) for req in requests_list],
            'count': len(requests_list)
        }), 200

    except Exception as e:
        logger.error(f"Error getting pending requests: {e}")
        return jsonify({'error': 'Failed to get requests'}), 500
    finally:
        if conn:
            conn.close()

# ===== EMAIL HELPER FUNCTION =====

def send_connection_email(recipient_email, recipient_name, sender_name, sender_role, action):
    """
    Send connection-related emails
    Actions: 'request', 'accepted', 'rejected', 'mutual'
    """
    try:
        if action == 'request':
            subject = f'🤝 New Connection Request from {sender_name}'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #1e3a8a; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.8rem;">🤝 New Connection Request!</h1>

                    <div style="background: linear-gradient(135deg, rgba(30, 58, 138, 0.1) 0%, rgba(14, 165, 233, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #0ea5e9;">
                        <p style="margin: 0 0 8px 0; color: #0ea5e9; font-weight: 700; font-size: 0.9rem;">📱 ALUMNI HUB NETWORK</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">Someone wants to connect with you!</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                    <h3 style="color: #1e3a8a; margin: 0 0 20px 0; font-size: 1.2rem;">👤 Connection Request Details</h3>

                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a; width: 30%;">From:</td>
                            <td style="padding: 12px 0; color: #333; font-size: 1.1rem; font-weight: 600;">{sender_name}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Role:</td>
                            <td style="padding: 12px 0; color: #333;"><span style="background: #e0e7ff; color: #1e3a8a; padding: 4px 10px; border-radius: 20px; font-size: 0.9rem; font-weight: 600;">{sender_role.upper()}</span></td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Date:</td>
                            <td style="padding: 12px 0; color: #666; font-size: 0.9rem;">{datetime.now().strftime('%d %B %Y at %I:%M %p')}</td>
                        </tr>
                    </table>
                </div>

                <div style="background: linear-gradient(135deg, #1e3a8a 0%, #0ea5e9 100%); padding: 25px; border-radius: 12px; margin-bottom: 15px; color: white; text-align: center;">
                    <p style="margin: 0 0 15px 0; font-size: 1rem; font-weight: 600;">👇 Accept or Reject This Request</p>
                    <p style="margin: 0; font-size: 0.9rem; opacity: 0.95;">Visit your dashboard to manage the request</p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        elif action == 'accepted':
            subject = f'✓ Your Connection Request to {recipient_name} Was Accepted!'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #10b981; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #10b981; margin: 0 0 15px 0; font-size: 1.8rem;">✓ Connection Accepted!</h1>

                    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(10, 150, 105, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #10b981;">
                        <p style="margin: 0 0 8px 0; color: #10b981; font-weight: 700; font-size: 0.9rem;">🎉 GREAT NEWS!</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">You're now connected!</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #10b981;">
                    <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">Happy to Connect 🤝</h3>
                    <p style="color: #333; line-height: 1.8; margin: 0;">
                        Great news! <strong>{recipient_name}</strong> (who is a {sender_role}) has accepted your connection request. You are now connected in the Alumni Hub network!
                    </p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        elif action == 'rejected':
            subject = f'Connection Request Update from {recipient_name}'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #f59e0b; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #f59e0b; margin: 0 0 15px 0; font-size: 1.8rem;">📋 Request Update</h1>

                    <div style="background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #f59e0b;">
                        <p style="margin: 0 0 8px 0; color: #f59e0b; font-weight: 700; font-size: 0.9rem;">STATUS UPDATE</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">Your connection request was not accepted</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b;">
                    <p style="color: #333; line-height: 1.8; margin: 0;">
                        Your connection request to <strong>{recipient_name}</strong> was declined. You can try connecting with other members of the Alumni Hub network!
                    </p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        elif action == 'mutual':
            subject = f'🎉 You\'re Now Connected with {sender_name}!'
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #f0f4ff 0%, #f8f9ff 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 30px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #10b981; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #10b981; margin: 0 0 15px 0; font-size: 1.8rem;">🎉 Mutual Connection!</h1>

                    <div style="background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(10, 150, 105, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #10b981;">
                        <p style="margin: 0 0 8px 0; color: #10b981; font-weight: 700; font-size: 0.9rem;">🌟 INSTANT CONNECTION!</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.1rem; font-weight: 800;">Mutual connection established!</p>
                    </div>
                </div>

                <div style="background: white; padding: 25px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #10b981;">
                    <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">Instant Match! 🤝</h3>
                    <p style="color: #333; line-height: 1.8; margin: 0;">
                        You and <strong>{sender_name}</strong> (who is a {sender_role}) have automatically become connected! You both wanted to connect with each other, so the system instantly established your connection.
                    </p>
                </div>

                <div style="background: #f0f4ff; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #1e3a8a;">Alumni Hub Management System</strong><br>
                        Building Connections, Creating Opportunities<br>
                        © 2026 Alumni Hub. All rights reserved.
                    </p>
                </div>
            </div>
            '''

        else:
            return  # Unknown action

        # Send email using the new send_email function
        success, message = send_email(recipient_email, subject, html_content)
        if not success:
            print(f"Warning: Connection email failed - {message}")

    except Exception as e:
        print(f"Error sending connection email: {e}")
        # Silently fail - don't interrupt request flow if email fails

# --- INFORMATION PAGES ---

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('common/privacy_policy.html')

@app.route('/terms-conditions')
def terms_conditions():
    return render_template('common/terms_conditions.html')

@app.route('/faq')
def faq():
    return render_template('common/faq.html')

@app.route('/report-issue', methods=['GET', 'POST'])
def report_issue():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        issue_type = request.form.get('issue_type', '').strip()
        description = request.form.get('description', '').strip()
        
        if not all([name, email, issue_type, description]):
            flash('All fields are required!', 'warning')
            return render_template('common/report_issue.html')
        
        # Send email to admin using send_email function
        try:
            submission_time = datetime.now().strftime('%d %B %Y at %I:%M %p')
            
            html_content = f'''
            <div style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; background: linear-gradient(135deg, #fef2f2 0%, #fff5f5 100%); padding: 30px; border-radius: 15px;">
                <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 20px; border-top: 5px solid #dc2626; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <h1 style="color: #dc2626; margin: 0 0 15px 0; font-size: 1.8rem;">🚨 New Issue Reported</h1>

                    <div style="background: linear-gradient(135deg, rgba(220, 38, 38, 0.1) 0%, rgba(239, 68, 68, 0.1) 100%); padding: 15px; border-radius: 8px; margin-bottom: 20px; border-left: 4px solid #ef4444;">
                        <p style="margin: 0 0 8px 0; color: #dc2626; font-weight: 700; font-size: 0.9rem;">📌 PROJECT SOURCE</p>
                        <p style="margin: 0; color: #1e3a8a; font-size: 1.2rem; font-weight: 800;">🎓 ALUMNI HUB MANAGEMENT SYSTEM</p>
                        <p style="margin: 5px 0 0 0; color: #666; font-size: 0.85rem;">Issue Report Submission</p>
                    </div>
                </div>

                <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                    <h3 style="color: #1e3a8a; margin: 0 0 15px 0; border-bottom: 2px solid #dc2626; padding-bottom: 10px; font-size: 1.1rem;">👤 Reporter Information</h3>

                    <table style="width: 100%; border-collapse: collapse;">
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a; width: 30%;">Name:</td>
                            <td style="padding: 12px 0; color: #333;">{name}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Email:</td>
                            <td style="padding: 12px 0; color: #333;"><a href="mailto:{email}" style="color: #0ea5e9; text-decoration: none; font-weight: 600;">{email}</a></td>
                        </tr>
                        <tr style="border-bottom: 1px solid #e5e7eb;">
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Issue Type:</td>
                            <td style="padding: 12px 0; color: #333;">
                                <span style="background: #dc2626; color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; font-weight: 600;">{issue_type}</span>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 12px 0; padding-right: 20px; font-weight: 700; color: #1e3a8a;">Submitted:</td>
                            <td style="padding: 12px 0; color: #666; font-size: 0.9rem;">{submission_time}</td>
                        </tr>
                    </table>
                </div>

                <div style="background: white; padding: 20px; border-radius: 12px; margin-bottom: 15px; border-left: 4px solid #f59e0b; box-shadow: 0 3px 10px rgba(0,0,0,0.08);">
                    <h3 style="color: #1e3a8a; margin: 0 0 15px 0; font-size: 1.1rem;">📝 Issue Description</h3>
                    <p style="margin: 0; color: #333; line-height: 1.8; white-space: pre-wrap; word-wrap: break-word;">{description}</p>
                </div>

                <div style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white; text-align: center;">
                    <p style="margin: 0; font-size: 0.95rem; font-weight: 600;">⚡ Action Required</p>
                    <p style="margin: 10px 0 0 0; font-size: 0.85rem; opacity: 0.9;">Please review and respond to this issue report promptly</p>
                </div>

                <div style="background: #fef2f2; padding: 15px; border-radius: 8px; text-align: center;">
                    <p style="margin: 0; color: #666; font-size: 0.85rem;">
                        <strong style="color: #dc2626;">Alumni Hub</strong> • Issue Tracking System<br>
                        This report was submitted via the Alumni Hub issue reporting form.
                    </p>
                </div>
            </div>
            '''
            
            admin_email = app.config.get('ADMIN_EMAIL', 'alumnihub26@gmail.com')
            success, msg_text = send_email(admin_email, f'🚨 Issue Report: {issue_type}', html_content)
            
            if success:
                flash('Issue reported successfully! We will get back to you soon.', 'success')
            else:
                flash(f'Error sending report: {msg_text}', 'danger')
            
            return redirect(url_for('report_issue'))

        except Exception as e:
            print(f"Error sending issue report: {e}")
            flash('Error sending report. Please try again.', 'danger')
    
    return render_template('common/report_issue.html')


@app.route('/contact/whatsapp/<int:user_id>')
@login_required
def whatsapp_bridge(user_id):
    """Secure bridge for WhatsApp redirection."""
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT id, name, phone FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user or not user['phone']:
            flash('Contact number not available.', 'danger')
            return redirect(request.referrer or url_for('home'))
            
        return render_template('contact_bridge.html', target_user=user)
    finally:
        if conn:
            conn.close()


@app.route('/contact/whatsapp/jump/<int:user_id>')
@login_required
def whatsapp_jump(user_id):
    """Final redirection jump for WhatsApp."""
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT phone FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user or not user['phone']:
            flash('Contact number not available.', 'danger')
            return redirect(url_for('home'))
            
        clean_phone = user['phone'].replace(' ', '').replace('+', '').replace('-', '')
        return redirect(f"https://wa.me/{clean_phone}")
    finally:
        if conn:
            conn.close()


@app.route('/send-email', methods=['POST'])
@login_required
def send_user_email():
    recipient_email = request.form.get('recipient_email')
    subject = request.form.get('subject')
    message_body = request.form.get('message')
    
    if not all([recipient_email, subject, message_body]):
        flash('All fields are required!', 'warning')
        return redirect(request.referrer or url_for('home'))
        
    try:
        # Fetch sender additional info (LinkedIn, WhatsApp etc)
        conn = get_db_connection()
        sender_profile = None
        
        if current_user.role == 'alumni':
            sender_profile = conn.execute('SELECT linkedin_url FROM alumni_profile WHERE user_id = ?', (current_user.id,)).fetchone()
        elif current_user.role == 'student':
            sender_profile = conn.execute('SELECT bio FROM student_profile WHERE user_id = ?', (current_user.id,)).fetchone()
        
        conn.close()

        # Build interactive signature
        base_url = request.host_url.rstrip('/')
        profile_url = f"{base_url}/{current_user.role}/profile/{current_user.id}"
        
        # SECURE: Use bridge URL instead of raw wa.me link to hide phone number
        whatsapp_bridge_url = f"{base_url}/contact/whatsapp/{current_user.id}"
        
        linkedin_html = ""
        if current_user.role == 'alumni' and sender_profile and 'linkedin_url' in sender_profile.keys():
            if sender_profile['linkedin_url']:
                linkedin_html = f'<p style="margin-top: 15px; font-size: 13px; color: #6b7280;"><a href="{sender_profile["linkedin_url"]}" style="color: #3b82f6; text-decoration: none;">Connect on LinkedIn →</a></p>'

        # Enriched HTML Content
        html_content = f'''
        <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; max-width: 600px; margin: 0 auto; background-color: #f9fafb; border-radius: 16px; overflow: hidden; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);">
            <div style="background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); padding: 30px; text-align: center;">
                <h1 style="color: white; margin: 0; font-size: 24px; font-weight: 800; letter-spacing: 1px;">ALUMNI HUB</h1>
                <p style="color: rgba(255,255,255,0.8); margin-top: 5px; font-size: 14px;">Official Communication</p>
            </div>
            
            <div style="padding: 40px 30px; background: white;">
                <p style="color: #6b7280; font-size: 14px; text-transform: uppercase; font-weight: 700; margin-bottom: 20px; letter-spacing: 0.5px;">Message from {current_user.name}:</p>
                <div style="background: #f3f4f6; padding: 25px; border-radius: 12px; border-left: 4px solid #3b82f6; margin-bottom: 30px;">
                    <p style="margin: 0; color: #1f2937; line-height: 1.6; font-size: 16px; white-space: pre-wrap;">{message_body}</p>
                </div>
                
                <div style="border-top: 1px solid #f3f4f6; padding-top: 30px;">
                    <p style="color: #374151; font-weight: 700; font-size: 16px; margin-bottom: 20px;">Contact the Sender</p>
                    <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                        <a href="{profile_url}" style="display: inline-block; padding: 12px 20px; background-color: #3b82f6; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px;">View Hub Profile</a>
                        <a href="{whatsapp_bridge_url}" style="display: inline-block; padding: 12px 20px; background-color: #25D366; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px;">WhatsApp Message</a>
                        <a href="mailto:{current_user.email}" style="display: inline-block; padding: 12px 20px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; font-weight: 600; font-size: 14px;">Reply via Email</a>
                    </div>
                    {linkedin_html}
                </div>
            </div>
            
            <div style="background-color: #f9fafb; padding: 20px; text-align: center; border-top: 1px solid #e5e7eb;">
                <p style="color: #9ca3af; font-size: 12px; margin: 0;">Sent via <a href="{base_url}" style="color: #3b82f6; text-decoration: none; font-weight: 600;">Alumni Hub</a></p>
                <p style="color: #9ca3af; font-size: 11px; margin-top: 5px;">This is an authenticated message sent directly from our secure portal.</p>
            </div>
        </div>
        '''
        
        success, msg_text = send_email(recipient_email, f"[Alumni Hub] {subject}", html_content)
        
        if success:
            flash('Email sent successfully!', 'success')
        else:
            flash(f'Failed to send email: {msg_text}', 'danger')
    except Exception as e:
        print(f"Error sending email: {e}")
        flash('Failed to send email. Please try again later.', 'danger')
        
    return redirect(request.referrer or url_for('home'))


@app.route('/compose-email/<int:user_id>')
@login_required
def compose_email(user_id):
    conn = None
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT id, name, email FROM users WHERE id = ?', (user_id,)).fetchone()
        
        if not user:
            flash('User not found!', 'danger')
            return redirect(url_for('home'))
            
        return render_template('compose_email.html', recipient=user)
    finally:
        if conn:
            conn.close()



# --- PUBLIC & SHARED ROUTES ---

@app.route('/events')
def events():
    if current_user.is_authenticated and current_user.role == 'faculty':
        return render_template('faculty/events.html')
    return render_template('events.html')

# Removed - moved to student-specific routes below



# --- STUDENT ROUTES ---

# Student-specific routes - all use student folder templates
@app.route('/network')
@login_required
def network():
    if current_user.role not in ['student', 'faculty', 'alumni']:
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    return render_template('student/network.html')

@app.route('/messages')
@login_required
def messages():
    if current_user.role not in ['student', 'faculty', 'alumni']:
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    return render_template('student/messages.html')

@app.route('/mentorship')
@login_required
def mentorship():
    if current_user.role != 'student':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    return render_template('student/mentorship.html')

@app.route('/notifications')
@login_required
def notifications():
    if current_user.role == 'faculty':
        return render_template('faculty/notifications.html')
    if current_user.role == 'student':
        return render_template('student/notifications.html')
    flash('Access denied!', 'danger')
    return redirect(url_for('home'))

@app.route('/settings')
@login_required
def settings():
    if current_user.role == 'faculty':
        return render_template('faculty/settings.html')
    if current_user.role == 'student':
        return render_template('student/settings.html')
    flash('Access denied!', 'danger')
    return redirect(url_for('home'))

# --- ALUMNI ROUTES ---

@app.route('/post-job', methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.role not in ('alumni', 'faculty'):
        flash('Only Alumni and Faculty can post jobs!', 'danger')
        return redirect(url_for('home'))
        
    if request.method == 'POST':
        title = request.form.get('title')
        company = request.form.get('company')
        location = request.form.get('location')
        salary = request.form.get('salary')
        job_type = request.form.get('job_type')
        apply_link = request.form.get('apply_link')
        description = request.form.get('description')
        skills = request.form.get('skills')
        category = request.form.get('category')
        deadline = request.form.get('deadline')
        
        # New Fields
        work_mode = request.form.get('work_mode', 'Onsite')
        eligible_branch = request.form.get('eligible_branch', 'All Branches')
        experience_required = request.form.get('experience_required', 'Freshers')
        employment_type = request.form.get('employment_type', 'Full-time')
        
        if not title or not company:
            flash('Title and Company are required!', 'warning')
            return redirect(url_for('post_job'))
            
        # Handle Logo Upload
        logo_path = None
        if 'company_logo' in request.files:
            file = request.files['company_logo']
            if file and file.filename != '':
                if allowed_file(file.filename):
                    filename = secure_filename(f"{int(time.time())}_{file.filename}")
                    full_path = os.path.join('static/uploads/company_logos', filename)
                    file.save(full_path)
                    logo_path = '/' + full_path.replace('\\', '/')
            
        conn = get_db_connection()
        c = conn.cursor()
        c.execute('''
            INSERT INTO jobs (
                title, company, location, salary, job_type, 
                apply_link, description, required_skills, posted_by, 
                company_logo, category, deadline,
                work_mode, eligible_branch, experience_required, employment_type,
                approval_status, posted_by_role
            ) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            title, company, location, salary, job_type, 
            apply_link, description, skills, current_user.id, 
            logo_path, category, deadline,
            work_mode, eligible_branch, experience_required, employment_type,
            'pending', current_user.role
        ))
        conn.commit()
        conn.close()
        
        flash('Job submitted for admin approval! It will be visible to students once approved.', 'success')
        if current_user.role == 'alumni':
            return redirect(url_for('dashboard_alumni'))
        return redirect(url_for('faculty_dashboard'))
        
    return render_template('alumni/post_job.html')

@app.route('/jobs')
@login_required
def list_jobs():
    if current_user.role not in ['student', 'alumni', 'faculty']:
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
        
    conn = get_db_connection()
    c = conn.cursor()
    today = datetime.now().strftime('%Y-%m-%d')

    # Active jobs: approved + (no deadline OR deadline >= today)
    active_jobs = c.execute('''
        SELECT j.*, u.name as posted_by_name 
        FROM jobs j 
        LEFT JOIN users u ON j.posted_by = u.id 
        WHERE j.is_active = 1
          AND (j.approval_status = 'approved' OR j.approval_status IS NULL)
          AND (j.deadline IS NULL OR j.deadline = '' OR j.deadline >= ?)
        ORDER BY j.created_at DESC
    ''', (today,)).fetchall()

    # Previous / expired jobs: approved + deadline has passed
    previous_jobs = c.execute('''
        SELECT j.*, u.name as posted_by_name 
        FROM jobs j 
        LEFT JOIN users u ON j.posted_by = u.id 
        WHERE j.is_active = 1
          AND (j.approval_status = 'approved' OR j.approval_status IS NULL)
          AND j.deadline IS NOT NULL AND j.deadline != '' AND j.deadline < ?
        ORDER BY j.deadline DESC
    ''', (today,)).fetchall()

    # Use modular recommendation logic
    recommended = get_recommended_jobs(current_user)
    conn.close()
    
    if current_user.role == 'alumni':
        return render_template('alumni/jobs.html',
                               jobs=active_jobs,
                               previous_jobs=previous_jobs,
                               recommended=recommended)
    if current_user.role == 'faculty':
        return render_template('alumni/jobs.html',
                               jobs=active_jobs,
                               previous_jobs=previous_jobs,
                               recommended=recommended)
    return render_template('student/jobs.html',
                           jobs=active_jobs,
                           previous_jobs=previous_jobs,
                           recommended=recommended)

@app.route('/spotlight')
@login_required
def spotlight():
    if current_user.role != 'alumni':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    return render_template('spotlight.html')

# --- FACULTY/ADMIN ROUTES ---

@app.route('/announcements')
@login_required
def announcements():
    if current_user.role == 'faculty':
        return render_template('faculty/announcements.html')
    if current_user.role == 'admin':
        return render_template('announcements.html')
    flash('Access denied!', 'danger')
    return redirect(url_for('home'))

@app.route('/reports')
@login_required
def reports():
    if current_user.role == 'faculty':
        return render_template('faculty/reports.html')
    if current_user.role == 'admin':
        return render_template('admin/reports.html')
    flash('Access denied!', 'danger')
    return redirect(url_for('home'))

# --- ADMIN ROUTES ---



@app.route('/api/approve-user/<int:user_id>', methods=['POST'])
@login_required
def approve_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    try:
        conn.execute('UPDATE users SET is_approved = 1 WHERE id = ?', (user_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f'Error approving user {user_id}: {e}')
        return jsonify({'success': False, 'error': 'Operation failed'}), 500
    finally:
        conn.close()

@app.route('/api/reject-user/<int:user_id>', methods=['POST'])
@login_required
def reject_user(user_id):
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
    conn = get_db_connection()
    try:
        # Delete user and their profile (profile tables have CASCADE or we manually delete if needed)
        # Based on schema, we might need manual delete for profiles if not CASCADE
        conn.execute('DELETE FROM student_profile WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM alumni_profile WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM faculty_profile WHERE user_id = ?', (user_id,))
        conn.execute('DELETE FROM users WHERE id = ?', (user_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/admin/events')
@login_required
def admin_events():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/admin_events.html')

@app.route('/admin/stats')
@login_required
def admin_stats():
    if current_user.role != 'admin':
        flash('Access denied!', 'danger')
        return redirect(url_for('home'))
    return render_template('admin/admin_stats.html')


# Background Task: Every 2 days, remind all users to update their profile
@scheduler.task('interval', id='periodic_profile_reminder', days=2, misfire_grace_time=900)
def periodic_profile_reminder():
    with app.app_context():
        try:
            print(f"🚀 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting scheduled profile reminder scan...")
            conn = get_db_connection()
            # Handle row factory if not already set to dict-like
            conn.row_factory = sqlite3.Row
            users = conn.execute('SELECT name, email FROM users WHERE is_suspended = 0').fetchall()
            conn.close()
            
            if not users:
                print("⚠️ No active users found to remind.")
                return

            base_url = os.getenv('BASE_URL', 'http://localhost:5000')
            profile_url = f"{base_url}/profile"
            
            count = 0
            for user in users:
                name = user['name']
                email = user['email']
                
                subject = "Reminder: Keep Your DBIT Alumni Profile Shine!"
                html_content = f"""
                <div style="font-family: 'Segoe UI', Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 30px; background-color: #ffffff; border: 1px solid #f0f0f0; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                    <div style="text-align: center; margin-bottom: 25px;">
                        <span style="font-size: 24px; font-weight: bold; color: #0d6efd; letter-spacing: 1px;">ALUMNI HUB</span>
                        <div style="height: 3px; background: linear-gradient(90deg, #0d6efd, #6610f2); width: 60px; margin: 8px auto 0;"></div>
                    </div>
                    
                    <h3 style="color: #333;">Hello {name},</h3>
                    
                    <p style="color: #555; line-height: 1.6; font-size: 16px;">
                        We noticed it's been a while since you last updated your profile. To make the most of the <strong>ALUMNI HUB</strong> and get the best career recommendations, please ensure your academic and professional details are current.
                    </p>
                    
                    <div style="text-align: center; margin: 40px 0;">
                        <a href="{profile_url}" 
                           style="background: linear-gradient(135deg, #0d6efd, #6610f2); color: #ffffff; padding: 15px 35px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 16px; display: inline-block; box-shadow: 0 4px 15px rgba(13, 110, 253, 0.3); transition: transform 0.2s;">
                           Update My Profile Now
                        </a>
                    </div>
                    
                    <p style="color: #666; font-size: 14px; line-height: 1.6;">
                        A complete profile unlocks better networking opportunities and helps you stay connected with your batchmates and mentors.
                    </p>
                    
                    <hr style="border: 0; border-top: 1px solid #eee; margin: 30px 0;">
                    
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        This is an automated periodic reminder. If you've recently updated your details, please ignore this message.
                    </p>
                </div>
                """
                send_email(email, subject, html_content)
                count += 1
            
            print(f"✅ [{datetime.now().strftime('%H:%M:%S')}] Periodic reminders successfully sent to {count} users.")
            
        except Exception as e:
            print(f"❌ Error in periodic_profile_reminder task: {e}")
            import traceback
            traceback.print_exc()

# --- Register Modular Blueprints (module-level for Gunicorn/production compatibility) ---
try:
    from routes.messaging_routes import messaging_bp
    from routes.websocket_routes import setup_websocket_handlers
    from routes.social_routes import social_bp
    from routes.connection_routes import connection_bp
    from routes.recommendation_routes import recommendation_bp

    if messaging_bp.name not in app.blueprints:
        app.register_blueprint(messaging_bp, url_prefix='/api')
    
    setup_websocket_handlers(socketio)

    if social_bp.name not in app.blueprints:
        app.register_blueprint(social_bp)

    if connection_bp.name not in app.blueprints:
        app.register_blueprint(connection_bp)
        
    if recommendation_bp.name not in app.blueprints:
        app.register_blueprint(recommendation_bp)
        
except Exception as e:
    logger.warning(f"Blueprint registration error: {e}")

# Initialize ML Recommendation Engine
try:
    from services.recommendation_engine import init_recommendation_engine
    init_recommendation_engine(app=app)
except Exception as e:
    logger.warning(f"ML recommendation engine init skipped: {e}")


# Ensure DB migrations always run (works with both `python app.py` and gunicorn)
with app.app_context():
    try:
        init_db()
    except Exception as _init_err:
        logger.warning(f"init_db warning: {_init_err}")

if __name__ == '__main__':
    pass  # init_db already called above

    print("\n" + "="*50)
    print("ALUMNI HUB IS STARTING UP...")
    print("Access the project at: http://127.0.0.1:5000")
    print("="*50 + "\n")
    
    socketio.run(app, debug=app.config['DEBUG'], host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
