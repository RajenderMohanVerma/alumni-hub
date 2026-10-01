from app import app, get_recommended_users, User
from db_utils import get_db_connection
import sqlite3

def run_tests():
    with app.app_context():
        conn = get_db_connection()
        c = conn.cursor()

        # Create a dummy user for testing
        test_user = User(
            id=999, 
            name="Test Student", 
            email="test@student.com", 
            role="student", 
            profile_pic=None,
            branch="Computer Science",
            skills="Python, Flask",
            city="Mumbai"
        )

        print("\n--- Testing Recommendation Scoring ---")
        # Ensure there is at least one alumni with matching branch
        alum = c.execute("SELECT id FROM users WHERE role='alumni'").fetchone()
        if alum:
            c.execute("UPDATE users SET branch='Computer Science', skills='Python' WHERE id=?", (alum['id'],))
            conn.commit()
        
        recs = get_recommended_users(test_user)
        
        if recs:
            print(f"✓ Found {len(recs)} recommendations")
            for r in recs:
                print(f"  - {r['name']} (Score: {r['score']}, Branch: {r['branch']}, Skills: {r['skills']})")
        else:
            print("✗ No recommendations found (Check if database has alumni users)")

        print("\n--- Testing Exclusion Logic ---")
        if recs:
            target_id = recs[0]['id']
            # Add to connections
            print(f"Adding connection with user {target_id}...")
            c.execute("INSERT INTO connections (user_id_1, user_id_2) VALUES (?, ?)", (test_user.id, target_id))
            conn.commit()
            
            recs_after = get_recommended_users(test_user)
            found = any(r['id'] == target_id for r in recs_after)
            if not found:
                print(f"✓ User {target_id} correctly excluded after connection")
            else:
                print(f"✗ User {target_id} still present after connection")
            
            # Clean up connection
            c.execute("DELETE FROM connections WHERE user_id_1 = ? AND user_id_2 = ?", (test_user.id, target_id))
            conn.commit()

        print("\n--- Testing Role-Based Filtering ---")
        # Alumni should not be recommended to Alumni (in this specific system, they want students)
        alumni_test_user = User(998, "Test Alumni", "test@alumni.com", "alumni", None)
        alumni_recs = get_recommended_users(alumni_test_user)
        student_count = sum(1 for r in alumni_recs if r['role'] == 'student')
        if student_count == len(alumni_recs):
            print("✓ Only students recommended to alumni")
        else:
            print(f"✗ Found non-student recommendations for alumni: {[r['role'] for r in alumni_recs]}")

    print("\nVerification Complete!")

if __name__ == "__main__":
    run_tests()
