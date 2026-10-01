import sqlite3
from app import app
from db_utils import get_db_connection

def migrate():
    with app.app_context():
        conn = get_db_connection()
        c = conn.cursor()

        print("Checking for new columns...")
        columns = [
            ("branch", "TEXT"),
            ("passing_year", "INTEGER"),
            ("current_domain", "TEXT"),
            ("skills", "TEXT"),
            ("interests", "TEXT"),
            ("city", "TEXT"),
            ("company", "TEXT")
        ]

        for col_name, col_type in columns:
            try:
                c.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"Added column: {col_name}")
            except sqlite3.OperationalError:
                print(f"Column already exists: {col_name}")

        conn.commit()

        print("Syncing data from student_profile...")
        students = c.execute("SELECT user_id, department, skills FROM student_profile").fetchall()
        for s in students:
            c.execute("""
                UPDATE users 
                SET branch = ?, skills = ? 
                WHERE id = ?
            """, (s['department'], s['skills'], s['user_id']))
        
        print("Syncing data from alumni_profile...")
        alumni = c.execute("SELECT user_id, department, pass_year, company_name, work_location FROM alumni_profile").fetchall()
        for a in alumni:
            c.execute("""
                UPDATE users 
                SET branch = ?, passing_year = ?, company = ?, city = ? 
                WHERE id = ?
            """, (a['department'], a['pass_year'], a['company_name'], a['work_location'], a['user_id']))

        conn.commit()
        conn.close()
        print("Migration completed successfully!")

if __name__ == "__main__":
    migrate()
