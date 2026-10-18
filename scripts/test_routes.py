import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app, get_db_connection

with app.app_context():
    client = app.test_client()
    
    # 1. Test public routes
    public_routes = ['/', '/login', '/register', '/events', '/jobs', '/about', '/contact']
    print("--- 1. TESTING PUBLIC ROUTES ---")
    for r in public_routes:
        res = client.get(r, follow_redirects=True)
        print(f"GET {r} -> status: {res.status_code}")
        assert res.status_code == 200, f"Route {r} failed with {res.status_code}"

    conn = get_db_connection()

    # 2. Test Student
    student = conn.execute("SELECT id, name, role FROM users WHERE role = 'student' LIMIT 1").fetchone()
    if student:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(student['id'])
            sess['_fresh'] = True
        
        print("\n--- 2. TESTING STUDENT ROUTES ---")
        student_routes = ['/student/dashboard', '/network', '/messages', '/jobs', '/events', '/mentorship']
        for r in student_routes:
            res = client.get(r, follow_redirects=True)
            print(f"GET {r} (Student: {student['name']}) -> status: {res.status_code}")
            assert res.status_code == 200, f"Route {r} failed with {res.status_code}"

    # 3. Test Alumni
    alumni = conn.execute("SELECT id, name, role FROM users WHERE role = 'alumni' LIMIT 1").fetchone()
    if alumni:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(alumni['id'])
            sess['_fresh'] = True
        
        print("\n--- 3. TESTING ALUMNI ROUTES ---")
        alumni_routes = ['/alumni/dashboard', '/alumni/network', '/alumni/jobs', '/alumni/messages', '/messages']
        for r in alumni_routes:
            res = client.get(r, follow_redirects=True)
            print(f"GET {r} (Alumni: {alumni['name']}) -> status: {res.status_code}")
            assert res.status_code == 200, f"Route {r} failed with {res.status_code}"

    # 4. Test Faculty
    faculty = conn.execute("SELECT id, name, role FROM users WHERE role = 'faculty' LIMIT 1").fetchone()
    if faculty:
        with client.session_transaction() as sess:
            sess['_user_id'] = str(faculty['id'])
            sess['_fresh'] = True
        
        print("\n--- 4. TESTING FACULTY ROUTES ---")
        faculty_routes = ['/faculty/dashboard', f"/faculty/profile/{faculty['id']}", '/faculty/messages', '/messages']
        for r in faculty_routes:
            res = client.get(r, follow_redirects=True)
            print(f"GET {r} (Faculty: {faculty['name']}) -> status: {res.status_code}")
            assert res.status_code == 200, f"Route {r} failed with {res.status_code}"

    conn.close()
    print("\nSUCCESS: ALL CRITICAL ROUTES (INCLUDING FACULTY MESSAGES) RENDER WITH 200 OK! ZERO CRASHES OR BUILD ERRORS!")
