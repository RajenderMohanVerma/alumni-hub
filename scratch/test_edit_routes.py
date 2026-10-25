import sys, os
sys.path.insert(0, os.path.abspath('.'))
from app import app, get_db_connection

with app.app_context():
    client = app.test_client()
    conn = get_db_connection()
    roles_routes = [
        ('admin', lambda u: f"/admin/profile/{u['id']}/edit"),
        ('student', lambda u: f"/student/profile/{u['id']}/edit"),
        ('alumni', lambda u: f"/alumni/profile/{u['id']}/edit"),
        ('faculty', lambda u: f"/faculty/profile/{u['id']}/edit"),
    ]
    for role, route_getter in roles_routes:
        u = conn.execute("SELECT id, name, role FROM users WHERE role = ? LIMIT 1", (role,)).fetchone()
        if u:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(u['id'])
                sess['_fresh'] = True
            target = route_getter(u)
            res = client.get(target, follow_redirects=True)
            print(f"{role.upper()} edit route {target} -> {res.status_code}")
            assert res.status_code == 200, f"{role} failed with {res.status_code}"
    print("\nALL 4 EDIT PROFILE ROUTES RETURN 200 OK!")
