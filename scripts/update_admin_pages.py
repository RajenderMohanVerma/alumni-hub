import os
import re

admin_dir = 'templates/admin'

# 1. Common sci-fi and robotic phrase replacements
text_replacements = [
    (re.compile(r'Return to Matrix', re.IGNORECASE), 'Back to Jobs Dashboard'),
    (re.compile(r'Career Nodes Matrix', re.IGNORECASE), 'Job Management Portal'),
    (re.compile(r'Neural Matrix Static', re.IGNORECASE), 'No Records Found'),
    (re.compile(r'The registration matrix is currently empty', re.IGNORECASE), 'No registrations found'),
    (re.compile(r'Professional nexus directory', re.IGNORECASE), 'Professional alumni directory'),
]

# 2. Modern Theme CSS Snippet for Dark-Default admin pages (admin_view_users, admin_approve_requests, admin_analytics, etc.)
light_theme_addon = """
    /* --- Modern Home-Card Container & Light/Dark Theme System --- */
    .glass-card, .matrix-card, .admin-card, .stat-card-premium {
        position: relative !important;
        border-radius: 18px !important;
        overflow: hidden !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }
    .glass-card::before, .matrix-card::before, .admin-card::before, .stat-card-premium::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 3px !important;
        background: linear-gradient(90deg, #6366f1, #a855f7) !important;
        opacity: 0.9 !important;
    }
    .glass-card:hover, .matrix-card:hover, .admin-card:hover {
        transform: translateY(-4px) !important;
    }

    [data-theme="light"] {
        --terminal-bg: #f8fafc;
        --glass-bg: rgba(255, 255, 255, 0.95);
        --glass-border: #e2e8f0;
        --text-dim: #64748b;
    }
    [data-theme="light"] body {
        background: #f8fafc !important;
        color: #0f172a !important;
    }
    [data-theme="light"] .premium-bg {
        background: linear-gradient(135deg, #f8fafc 0%, #eff6ff 100%) !important;
    }
    [data-theme="light"] .glass-card,
    [data-theme="light"] .matrix-card,
    [data-theme="light"] .admin-card,
    [data-theme="light"] .stat-card,
    [data-theme="light"] .directory-module,
    [data-theme="light"] .form-matrix,
    [data-theme="light"] .card-terminal {
        background: #ffffff !important;
        border: 1px solid #e2e8f0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05) !important;
        color: #0f172a !important;
    }
    [data-theme="light"] .matrix-title,
    [data-theme="light"] .matrix-value,
    [data-theme="light"] .text-white,
    [data-theme="light"] h1, 
    [data-theme="light"] h2, 
    [data-theme="light"] h3, 
    [data-theme="light"] h4, 
    [data-theme="light"] h5, 
    [data-theme="light"] h6 {
        color: #0f172a !important;
    }
    [data-theme="light"] .text-dim,
    [data-theme="light"] .text-white-50 {
        color: #64748b !important;
    }
    [data-theme="light"] .table {
        color: #0f172a !important;
    }
    [data-theme="light"] .table tr {
        border-color: #e2e8f0 !important;
    }
    [data-theme="light"] .table th {
        background: #f8fafc !important;
        color: #64748b !important;
    }
    [data-theme="light"] .table td {
        color: #0f172a !important;
    }
    [data-theme="light"] .form-control,
    [data-theme="light"] .form-select,
    [data-theme="light"] .command-input {
        background: #ffffff !important;
        border: 1px solid #cbd5e1 !important;
        color: #0f172a !important;
    }
    [data-theme="light"] .form-control:focus,
    [data-theme="light"] .form-select:focus,
    [data-theme="light"] .command-input:focus {
        border-color: #6366f1 !important;
        box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.15) !important;
    }
    [data-theme="light"] .stat-chip,
    [data-theme="light"] .glass-pill,
    [data-theme="light"] .action-chip {
        background: #f1f5f9 !important;
        border: 1px solid #e2e8f0 !important;
        color: #0f172a !important;
    }
    [data-theme="light"] .particles-bg,
    [data-theme="light"] .mesh-gradient {
        opacity: 0.15 !important;
    }
"""

# 3. Modern Theme CSS Snippet for Light-Default admin pages (dashboard_admin, jobs, add_job, edit_job)
dark_theme_addon = """
    /* --- Modern Home-Card Container & Dark Theme Support --- */
    .glass-card, .matrix-card, .admin-card, .stat-card-premium, .job-card-master, .directory-module {
        position: relative !important;
        border-radius: 18px !important;
        overflow: hidden !important;
        transition: transform 0.25s ease, box-shadow 0.25s ease !important;
    }
    .glass-card::before, .matrix-card::before, .stat-card-premium::before, .job-card-master::before {
        content: '' !important;
        position: absolute !important;
        top: 0 !important;
        left: 0 !important;
        right: 0 !important;
        height: 3px !important;
        background: linear-gradient(90deg, #6366f1, #a855f7) !important;
        opacity: 0.9 !important;
    }
    .glass-card:hover, .matrix-card:hover, .stat-card-premium:hover, .job-card-master:hover {
        transform: translateY(-4px) !important;
    }

    [data-theme="dark"] {
        --terminal-bg: #0b0f19;
        --dark-navy: #f8fafc;
        --dark-slate: #f8fafc;
        --soft-slate: #1e293b;
        --glass-white: #1e293b;
        --glass-bg: rgba(30, 41, 59, 0.85);
        --glass-border: rgba(255, 255, 255, 0.1);
        --text-main: #f8fafc;
        --text-dim: #94a3b8;
    }
    [data-theme="dark"] body {
        background: #0b0f19 !important;
        color: #f8fafc !important;
    }
    [data-theme="dark"] .premium-bg {
        background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%) !important;
    }
    [data-theme="dark"] .glass-card,
    [data-theme="dark"] .matrix-card,
    [data-theme="dark"] .directory-module,
    [data-theme="dark"] .stat-card-premium,
    [data-theme="dark"] .job-card-master,
    [data-theme="dark"] .filter-bar-floating,
    [data-theme="dark"] .form-container,
    [data-theme="dark"] .card-custom {
        background: #1e293b !important;
        border-color: #334155 !important;
        color: #f8fafc !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.25) !important;
    }
    [data-theme="dark"] .matrix-value,
    [data-theme="dark"] .matrix-title,
    [data-theme="dark"] .directory-title,
    [data-theme="dark"] .job-card-master h3,
    [data-theme="dark"] .job-card-master h4,
    [data-theme="dark"] .job-card-master h5,
    [data-theme="dark"] .stat-value,
    [data-theme="dark"] .text-slate-900 {
        color: #f8fafc !important;
    }
    [data-theme="dark"] .text-dim,
    [data-theme="dark"] .text-slate-500 {
        color: #94a3b8 !important;
    }
    [data-theme="dark"] .command-bar {
        background: rgba(15, 23, 42, 0.6) !important;
    }
    [data-theme="dark"] .command-input,
    [data-theme="dark"] .form-control,
    [data-theme="dark"] .form-select {
        background: #0f172a !important;
        border-color: #334155 !important;
        color: #f8fafc !important;
    }
    [data-theme="dark"] .table {
        color: #f8fafc !important;
    }
    [data-theme="dark"] .table tr {
        border-color: rgba(255, 255, 255, 0.08) !important;
    }
    [data-theme="dark"] .table th {
        background: #0f172a !important;
        color: #94a3b8 !important;
    }
    [data-theme="dark"] .table td {
        color: #f8fafc !important;
    }
    [data-theme="dark"] .bg-slate-100 {
        background-color: #1e293b !important;
    }
    [data-theme="dark"] .border-slate-200 {
        border-color: #334155 !important;
    }
"""

# Connection monitor addon
cm_addon = """
    /* --- Connection Monitor Dark Theme --- */
    [data-theme="dark"] {
        --cm-surface: #1e293b;
        --cm-border: rgba(255, 255, 255, 0.1);
        --cm-ink: #f8fafc;
        --cm-muted: #94a3b8;
    }
    [data-theme="dark"] body {
        background: #0b0f19 !important;
        color: #f8fafc !important;
    }
    [data-theme="dark"] .cm-card,
    [data-theme="dark"] .cm-table-wrap {
        background: #1e293b !important;
        border-color: #334155 !important;
        color: #f8fafc !important;
    }
"""

light_default_files = {'dashboard_admin.html', 'jobs.html', 'add_job.html', 'edit_job.html'}

for filename in sorted(os.listdir(admin_dir)):
    if not filename.endswith('.html'):
        continue
    filepath = os.path.join(admin_dir, filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Apply text replacements
    for pattern, repl in text_replacements:
        content = pattern.sub(repl, content)

    # Avoid duplicate injection
    if 'data-theme="light"' in content or 'data-theme="dark"' in content:
        continue

    # Determine which CSS snippet to inject
    if filename == 'connection_monitor.html':
        snippet = cm_addon
    elif filename in light_default_files:
        snippet = dark_theme_addon
    else:
        snippet = light_theme_addon

    # Inject snippet before </style> or inside style
    if '</style>' in content:
        # replace first </style>
        content = content.replace('</style>', snippet + '\n</style>', 1)
        print(f"Updated style in {filename}")
    else:
        # wrap in <style>
        content += f"\n<style>{snippet}</style>\n"
        print(f"Added style block in {filename}")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

print("\nAll 16 admin templates updated successfully!")
