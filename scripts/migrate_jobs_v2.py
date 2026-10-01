import sqlite3
import os

def migrate_v2():
    db_paths = ['data/college_pro.db', 'data/alumni.db']
    
    new_columns = [
        ('work_mode', 'TEXT'),
        ('employment_type', 'TEXT'),
        ('eligible_branch', 'TEXT'),
        ('eligible_batch', 'TEXT'),
        ('qualification', 'TEXT'),
        ('min_cgpa', 'TEXT'),
        ('experience_required', 'TEXT'),
        ('skills_preferred', 'TEXT'),
        ('perks', 'TEXT'),
        ('openings', 'INTEGER'),
        ('selection_process', 'TEXT'),
        ('joining_date', 'TEXT'),
        ('target_role', 'TEXT'),
        ('skill_level', 'TEXT'),
        ('apply_method', 'TEXT'),
        ('company_website', 'TEXT'),
        ('salary_perks', 'TEXT'),
        ('ctc_range', 'TEXT')
    ]
    
    for db_path in db_paths:
        if not os.path.exists(db_path):
            print(f"Skipping {db_path} - Not found")
            continue
            
        print(f"\n--- Migrating {db_path} ---")
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            
            # Get existing columns
            cursor = c.execute("PRAGMA table_info(jobs)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            for col_name, col_type in new_columns:
                if col_name not in existing_columns:
                    print(f"  + Adding {col_name} ({col_type})")
                    c.execute(f"ALTER TABLE jobs ADD COLUMN {col_name} {col_type}")
                else:
                    print(f"  - {col_name} already exists")
            
            # Check for name changes or other fields requested by user
            # User mentioned: company_name (already have company, but user asked for company_name in structure)
            if 'company_name' not in existing_columns:
                 c.execute("ALTER TABLE jobs ADD COLUMN company_name TEXT")
            
            # User mentioned: skills_required (we have required_skills, let's sync or duplicate for reliability)
            if 'skills_required' not in existing_columns:
                 c.execute("ALTER TABLE jobs ADD COLUMN skills_required TEXT")
                 
            # Add job_status if missing (user logic mentions it for backend)
            if 'job_status' not in existing_columns:
                 c.execute("ALTER TABLE jobs ADD COLUMN job_status TEXT DEFAULT 'Open'")
            
            conn.commit()
            conn.close()
            print(f"Successfully migrated {db_path}")
        except Exception as e:
            print(f"Error migrating {db_path}: {e}")

if __name__ == "__main__":
    migrate_v2()
