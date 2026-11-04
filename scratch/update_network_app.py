app_path = 'app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    code = f.read()

target = """    per_page = 16  # 16 members per page with next/prev pagination

    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', 'all').strip().lower()
    dept_filter = request.args.get('department', 'all').strip()
    loc_filter = request.args.get('location', 'all').strip()"""

replacement = """    per_page = 12  # Maximum 12 members per page with next/prev arrows

    scope_filter = request.args.get('scope', 'all').strip().lower()
    search_query = request.args.get('search', '').strip()
    role_filter = request.args.get('role', 'all').strip().lower()
    dept_filter = request.args.get('department', 'all').strip()
    loc_filter = request.args.get('location', 'all').strip()"""

if target in code:
    code = code.replace(target, replacement, 1)
    print("Target 1 replaced.")
else:
    print("Target 1 not found.")

target_where = """        # Dynamic Filtering on real DB records
        where_clauses = [
            "u.role IN ('student', 'alumni', 'faculty')",
            "(u.is_approved = 1 OR u.is_approved IS NULL)"
        ]
        params = []"""

replacement_where = """        # Dynamic Filtering on real DB records
        where_clauses = [
            "u.role IN ('student', 'alumni', 'faculty')",
            "(u.is_approved = 1 OR u.is_approved IS NULL)"
        ]
        params = []

        # If scope is 'connections', filter to only users connected to current user
        if scope_filter == 'connections':
            where_clauses.append('''u.id IN (
                SELECT CASE WHEN sender_id = ? THEN receiver_id ELSE sender_id END
                FROM connection_requests
                WHERE (sender_id = ? OR receiver_id = ?) AND status = 'accepted'
            )''')
            params.extend([current_user.id, current_user.id, current_user.id])"""

if target_where in code:
    code = code.replace(target_where, replacement_where, 1)
    print("Target 2 replaced.")
else:
    print("Target 2 not found.")

target_render = """                               selected_loc=loc_filter,
                               connected_user_ids=connected_user_ids,
                               pending_sent_ids=pending_sent_ids)"""

replacement_render = """                               selected_loc=loc_filter,
                               selected_scope=scope_filter,
                               connected_user_ids=connected_user_ids,
                               pending_sent_ids=pending_sent_ids)"""

if target_render in code:
    code = code.replace(target_render, replacement_render, 1)
    print("Target 3 replaced.")
else:
    print("Target 3 not found.")

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(code)

print("Finished updating app.py")

