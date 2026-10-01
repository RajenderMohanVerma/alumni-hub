import sqlite3
import os
from werkzeug.security import generate_password_hash

# Database path
DB_PATH = os.path.join('data', 'college_pro.db')

# Ensure data directory exists
if not os.path.exists('data'):
    os.makedirs('data')

# Delete old database if exists
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)
    print(f"Old database deleted at {DB_PATH}")

# Create new database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()

print("Creating database tables...")

# Create users table
c.execute('''CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    role TEXT NOT NULL,
    phone TEXT,
    profile_pic TEXT DEFAULT '',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)''')

# Create other tables (alumni_profile, student_profile, faculty_profile, etc.)
c.execute('''CREATE TABLE IF NOT EXISTS alumni_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    enrollment_no TEXT UNIQUE,
    department TEXT,
    degree TEXT,
    pass_year INTEGER,
    company_name TEXT,
    designation TEXT,
    work_location TEXT,
    experience_years INTEGER DEFAULT 0,
    linkedin_url TEXT,
    skills TEXT,
    achievements TEXT,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE IF NOT EXISTS student_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    enrollment_no TEXT UNIQUE,
    department TEXT,
    degree TEXT,
    semester INTEGER,
    cgpa REAL,
    skills TEXT,
    interests TEXT,
    achievements TEXT,
    resume_link TEXT,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE IF NOT EXISTS faculty_profile (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE,
    employee_id TEXT UNIQUE,
    department TEXT,
    designation TEXT,
    specialization TEXT,
    qualification TEXT,
    experience_years INTEGER DEFAULT 0,
    office_location TEXT,
    office_hours TEXT,
    bio TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE IF NOT EXISTS connection_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (receiver_id) REFERENCES users(id) ON DELETE CASCADE
)''')

c.execute('''CREATE TABLE IF NOT EXISTS connections (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER,
    user2_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (user2_id) REFERENCES users(id) ON DELETE CASCADE
)''')

# Create admin user with new credentials
print("Creating admin user...")
pw = generate_password_hash("admindbit195@")
c.execute("INSERT INTO users (name, email, password, role, phone) VALUES (?, ?, ?, ?, ?)",
          ("Super Admin", "admindbit195@college.edu", pw, "admin", "0000000000"))

conn.commit()
print("Database initialized successfully!")
print("\nAdmin credentials:")
print("Email: admindbit195@college.edu")
print("Password: admindbit195@")

# Verify tables
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = c.fetchall()
print(f"\nCreated tables: {[t[0] for t in tables]}")

conn.close()
