"""
PostgreSQL Database Initialization Script for Vercel
Run this once after setting up your PostgreSQL database on Neon/Supabase
"""

import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Get DATABASE_URL from environment
database_url = os.getenv('DATABASE_URL')

if not database_url:
    print("ERROR: DATABASE_URL not found in environment variables!")
    print("Please set DATABASE_URL in your .env file or Vercel dashboard")
    exit(1)

# Fix postgres:// to postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

print("Connecting to PostgreSQL...")
conn = psycopg2.connect(database_url, cursor_factory=RealDictCursor)
cursor = conn.cursor()

print("Creating tables...")

# Users table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        phone TEXT,
        role TEXT NOT NULL,
        profile_pic TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Student Profile Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS student_profile (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
        enrollment_no TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        degree TEXT NOT NULL,
        semester INTEGER,
        cgpa REAL,
        skills TEXT,
        achievements TEXT,
        resume_link TEXT
    )
''')

# Alumni Profile Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS alumni_profile (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
        enrollment_no TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        degree TEXT NOT NULL,
        pass_year INTEGER NOT NULL,
        company_name TEXT,
        designation TEXT,
        work_location TEXT,
        experience_years INTEGER,
        linkedin_url TEXT,
        github_url TEXT,
        portfolio_url TEXT,
        bio TEXT
    )
''')

# Faculty Profile Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS faculty_profile (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL UNIQUE REFERENCES users(id),
        employee_id TEXT UNIQUE NOT NULL,
        department TEXT NOT NULL,
        designation TEXT NOT NULL,
        specialization TEXT,
        qualification TEXT,
        experience_years INTEGER,
        office_location TEXT,
        office_hours TEXT,
        bio TEXT
    )
''')

# Connection Requests Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS connection_requests (
        id SERIAL PRIMARY KEY,
        sender_id INTEGER NOT NULL REFERENCES users(id),
        receiver_id INTEGER NOT NULL REFERENCES users(id),
        status TEXT DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

# Registration Log Table
cursor.execute('''
    CREATE TABLE IF NOT EXISTS registration_log (
        id SERIAL PRIMARY KEY,
        user_id INTEGER REFERENCES users(id),
        name TEXT,
        email TEXT,
        phone TEXT,
        role TEXT,
        enrollment_no TEXT,
        employee_id TEXT,
        department TEXT,
        degree TEXT,
        pass_year INTEGER,
        company_name TEXT,
        designation TEXT,
        experience_years INTEGER,
        registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
print("✅ Database initialized successfully!")

# Create default admin user if not exists
cursor.execute("SELECT * FROM users WHERE email = 'admin@alumni.com'")
admin = cursor.fetchone()

if not admin:
    from werkzeug.security import generate_password_hash
    
    print("Creating default admin user...")
    password_hash = generate_password_hash('admin123')
    
    cursor.execute('''
        INSERT INTO users (name, email, password, phone, role)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id
    ''', ('Admin', 'admin@alumni.com', password_hash, '1234567890', 'admin'))
    
    conn.commit()
    print("✅ Admin user created!")
    print("   Email: admin@alumni.com")
    print("   Password: admin123")
else:
    print("ℹ️  Admin user already exists")

cursor.close()
conn.close()
print("\n🎉 Setup complete! Your database is ready for Vercel deployment.")
