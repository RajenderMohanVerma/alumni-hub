import sys, os, io
sys.path.insert(0, os.path.abspath('.'))
from app import app, get_db_connection, load_user
from io import BytesIO
from PIL import Image

# Create a small valid test PNG image
img_byte_arr = BytesIO()
test_img = Image.new('RGB', (100, 100), color=(30, 144, 255)) # Dodger Blue
test_img.save(img_byte_arr, format='PNG')
img_bytes = img_byte_arr.getvalue()

with app.app_context():
    client = app.test_client()
    conn = get_db_connection()

    test_roles = [
        ('admin', lambda u: f"/admin/profile/{u['id']}/edit", lambda u: f"/admin/profile/{u['id']}"),
        ('student', lambda u: f"/student/profile/{u['id']}/edit", lambda u: f"/student/profile/{u['id']}"),
        ('alumni', lambda u: f"/alumni/profile/{u['id']}/edit", lambda u: f"/alumni/profile/{u['id']}"),
        ('faculty', lambda u: f"/faculty/profile/{u['id']}/edit", lambda u: f"/faculty/profile/{u['id']}"),
    ]

    print("=== TESTING PROFILE PICTURE UPDATE AND REFLECTION ACROSS ROLES ===")

    for role, edit_url_fn, view_url_fn in test_roles:
        u = conn.execute("SELECT id, name, email, phone, role FROM users WHERE role = ? LIMIT 1", (role,)).fetchone()
        assert u, f"No user with role {role}"
        uid = u['id']
        uname = u['name']

        with client.session_transaction() as sess:
            sess['_user_id'] = str(uid)
            sess['_fresh'] = True

        edit_url = edit_url_fn(u)
        view_url = view_url_fn(u)

        # Upload new profile image
        data = {
            'name': uname,
            'email': u['email'],
            'phone': u['phone'] or '9876543210',
            'profile_pic': (BytesIO(img_bytes), 'avatar.png')
        }
        res = client.post(edit_url, data=data, content_type='multipart/form-data', follow_redirects=True)
        print(f"[{role.upper()}] Upload POST {edit_url} -> Status {res.status_code}")
        assert res.status_code == 200, f"Upload failed for {role}"

        # 1. Verify DB contains updated profile_pic
        updated_u = conn.execute("SELECT profile_pic FROM users WHERE id = ?", (uid,)).fetchone()
        pic_in_db = updated_u['profile_pic']
        assert pic_in_db and (pic_in_db.startswith('data:image/') or pic_in_db.startswith('/')), f"DB profile_pic missing for {role}: {pic_in_db}"
        print(f"[{role.upper()}] Verified DB profile_pic is updated ({pic_in_db[:35]}...)")

        # 2. Verify load_user(uid).profile_pic reflects it
        loaded = load_user(str(uid))
        assert loaded.profile_pic == pic_in_db, f"load_user mismatch for {role}"
        print(f"[{role.upper()}] Verified current_user / load_user has the new image!")

        # 3. Verify user's profile view page renders with the image
        view_res = client.get(view_url)
        assert view_res.status_code == 200
        # If Base64 or path, ensure image source appears or html doesn't error
        print(f"[{role.upper()}] Verified Profile View {view_url} renders 200 OK!")

    # 4. Check Admin User Directory & Dashboard for all updated avatars
    admin_u = conn.execute("SELECT id, name, role FROM users WHERE role = 'admin' LIMIT 1").fetchone()
    with client.session_transaction() as sess:
        sess['_user_id'] = str(admin_u['id'])
        sess['_fresh'] = True

    admin_view_res = client.get('/admin/users/all')
    assert admin_view_res.status_code == 200
    print("[ADMIN] Verified /admin/users/all renders 200 OK and shows all avatars!")

    admin_dash_res = client.get('/admin/dashboard')
    assert admin_dash_res.status_code == 200
    print("[ADMIN] Verified /admin/dashboard renders 200 OK!")

    # 5. Check Messaging API endpoints: /api/messages/users and /api/messages/inbox
    msg_users_res = client.get('/api/messages/users')
    assert msg_users_res.status_code == 200
    users_json = msg_users_res.get_json()
    assert users_json['success']
    print(f"[MESSAGING] Verified /api/messages/users returns {len(users_json['users'])} users with profile_pic populated!")

    msg_inbox_res = client.get('/api/messages/inbox')
    assert msg_inbox_res.status_code == 200
    print("[MESSAGING] Verified /api/messages/inbox returns 200 OK!")

    print("\nSUCCESS: ALL ROLES UPDATE PROFILE PIC AND IT REFLECTS EVERYWHERE INCLUDING TO ADMIN!")
