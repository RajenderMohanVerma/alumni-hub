import sqlite3
import os

def migrate():
    conn = sqlite3.connect('college_pro.db')
    c = conn.cursor()
    
    print("Creating Job ecosystem tables...")
    
    # Create jobs table with new fields
    c.execute('''CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT NOT NULL,
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
    )''')

    # Migration logic for existing tables: check if new columns exist
    cursor = c.execute("PRAGMA table_info(jobs)")
    columns = [row[1] for row in cursor.fetchall()]
    
    new_columns = [
        ('location', 'TEXT'),
        ('salary', 'TEXT'),
        ('job_type', 'TEXT'),
        ('apply_link', 'TEXT'),
        ('is_active', 'INTEGER DEFAULT 1'),
        ('company_logo', 'TEXT'),
        ('deadline', 'TEXT'),
        ('category', 'TEXT')
    ]
    
    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"Adding column {col_name} to jobs table...")
            c.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
    
    # Create job_applications table (for tracking interest)
    c.execute('''CREATE TABLE IF NOT EXISTS job_applications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER,
        student_id INTEGER,
        status TEXT DEFAULT 'applied',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE CASCADE,
        FOREIGN KEY (student_id) REFERENCES users(id) ON DELETE CASCADE
    )''')
    
    conn.commit()
    conn.close()
    print("Job ecosystem tables created successfully!")

if __name__ == "__main__":
    migrate()
