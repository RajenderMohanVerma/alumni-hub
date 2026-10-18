import os
import re

target_files = [
    'templates/messaging/private_chat.html',
    'templates/messaging/dashboard.html',
    'templates/common/report_issue.html',
    'templates/admin/reports.html',
    'templates/admin/profile_admin.html',
    'templates/admin/edit_admin_profile.html',
    'templates/admin/admin_view_users.html',
    'templates/admin/admin_stats.html',
    'templates/admin/admin_registrations.html',
    'templates/admin/admin_messaging_control.html',
    'templates/admin/admin_events.html',
    'templates/admin/admin_approve_requests.html',
    'templates/admin/admin_analytics.html',
    'templates/admin/whatsapp_broadcast.html',
    'templates/admin/dashboard_admin.html',
    'templates/faculty/profile.html',
    'templates/faculty/edit_profile.html',
]

for rel_path in target_files:
    if not os.path.exists(rel_path):
        continue
    with open(rel_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Replace dark terminal bg with home page clean light bg
    content = content.replace('--terminal-bg: #030712;', '--terminal-bg: #f8fafc;')
    content = content.replace('--dark-bg: #030712;', '--dark-bg: #f8fafc;')
    content = content.replace('--dark-bg: #0b0f19;', '--dark-bg: #f8fafc;')
    content = content.replace('--glass-bg: rgba(15, 23, 42, 0.7);', '--glass-bg: #ffffff;')
    content = content.replace('--glass-bg: rgba(15, 23, 42, 0.6);', '--glass-bg: #ffffff;')
    content = content.replace('--glass-border: rgba(255, 255, 255, 0.1);', '--glass-border: #e1e7ed;')
    content = content.replace('--text-dim: #94a3b8;', '--text-dim: #64748b;')
    content = content.replace('color: white;', 'color: #0f172a;')
    content = content.replace('background: #060a16;', 'background: #f8fafc;')
    content = content.replace('background: var(--bg-primary, #060a16);', 'background: #f8fafc;')
    content = content.replace('color: var(--text-primary, #ffffff);', 'color: #0f172a;')
    
    # 2. In premium background: replace radial dark gradient with light mesh gradient
    content = content.replace(
        'background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%);',
        'background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);'
    )
    content = content.replace(
        'background: radial-gradient(circle at 50% 50%, #0f172a 0%, #030712 100%);',
        'background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%);'
    )

    with open(rel_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Updated {rel_path} to Home Page clean light theme")

print("All dark-default templates updated to clean Home Page light mode!")
