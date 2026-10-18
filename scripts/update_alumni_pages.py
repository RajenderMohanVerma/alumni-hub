import os
import re

def update_file(path, replacements, regex_replacements=None):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    for old, new in replacements:
        content = content.replace(old, new)

    if regex_replacements:
        for pattern, repl in regex_replacements:
            content = re.sub(pattern, repl, content)

    if content != original:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated {path}")
    else:
        print(f"No changes needed for {path}")

# 1. Update templates/alumni/profile.html
profile_replacements = [
    ('--glass-bg: rgba(255, 255, 255, 0.85);', '--glass-bg: var(--bg-surface);'),
    ('background: #f8fafc;', 'background: var(--bg-primary); color: var(--text-primary);'),
    ('background: white;', 'background: var(--bg-surface); color: var(--text-primary);'),
    ('bg-white border border-slate-100', 'border',),
    ('text-slate-900', 'text-theme-primary'),
    ('text-slate-800', 'text-theme-primary'),
    ('border: 1px solid rgba(0, 0, 0, 0.03);', 'border: 1px solid var(--border-color); border-radius: 18px;'),
    ('border: 10px solid white;', 'border: 6px solid var(--border-color);')
]
update_file('templates/alumni/profile.html', profile_replacements)

# 2. Update templates/alumni/edit_profile.html
edit_profile_replacements = [
    ('background: #0a0e27;', 'background: var(--bg-primary); color: var(--text-primary);'),
    ('background: rgba(255, 255, 255, 0.05);', 'background: var(--bg-surface); color: var(--text-primary);'),
    ('background: rgba(255, 255, 255, 0.08);', 'background: var(--bg-surface); color: var(--text-primary);'),
    ('border: 1px solid rgba(255, 255, 255, 0.1);', 'border: 1px solid var(--border-color);'),
    ('border: 2px solid rgba(255, 255, 255, 0.1);', 'border: 1px solid var(--border-color);'),
    ('border: 1px solid rgba(255, 255, 255, 0.15);', 'border: 1px solid var(--border-color);'),
    ('color: rgba(255, 255, 255, 0.9);', 'color: var(--text-primary);'),
    ('color: rgba(255, 255, 255, 0.8);', 'color: var(--text-secondary);'),
    ('color: rgba(255, 255, 255, 0.7);', 'color: var(--text-muted);'),
    ('color: white;', 'color: var(--text-primary);'),
    ('background: rgba(255, 255, 255, 0.03);', 'background: var(--bg-subtle);'),
    ('background: rgba(255, 255, 255, 0.02);', 'background: var(--bg-subtle);')
]
update_file('templates/alumni/edit_profile.html', edit_profile_replacements)

# 3. Update templates/alumni/dashboard.html
dashboard_replacements = [
    ('background-color: #f8fafc;', 'background-color: var(--bg-primary) !important; color: var(--text-primary) !important;'),
    ('background: #f8fafc;', 'background: var(--bg-primary);'),
    ('style="background:white;border:1px solid #e2e8f0;border-radius:20px;padding:18px 22px;box-shadow:0 2px 12px rgba(0,0,0,0.04);transition:all 0.3s ease;"', 'style="background:var(--bg-surface);border:1px solid var(--border-color);border-radius:18px;padding:18px 22px;box-shadow:var(--card-shadow);transition:all 0.3s ease;"'),
    ('style="color:#1e293b;"', 'style="color:var(--text-primary);"'),
    ('style="background: white; border: 1px solid #e2e8f0; border-radius: 24px;"', 'style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 18px;"'),
    ('btn-light-primary text-start p-3 rounded-4 transition-all hover-lift', 'btn text-start p-3 rounded-4 transition-all hover-lift" style="background: var(--bg-subtle); color: var(--text-primary); border: 1px solid var(--border-color);'),
    ('btn-light-warning text-start p-3 rounded-4 transition-all hover-lift', 'btn text-start p-3 rounded-4 transition-all hover-lift" style="background: var(--bg-subtle); color: var(--text-primary); border: 1px solid var(--border-color);'),
    ('class="stat-card"', 'class="stat-card home-card"')
]
update_file('templates/alumni/dashboard.html', dashboard_replacements)

# 4. Update templates/alumni/events.html
events_replacements = [
    ('background-color: #f8fafc;', 'background-color: var(--bg-primary) !important; color: var(--text-primary) !important;'),
    ('background: #f8fafc;', 'background: var(--bg-primary);'),
    ('color: #1e293b;\n        margin-bottom: 0.5rem;\n        text-shadow: 0 2px 4px rgba(255, 255, 255, 0.5);', 'color: #ffffff;\n        margin-bottom: 0.5rem;'),
    ('class="glass-card', 'class="home-card'),
    ('background: rgba(255, 255, 255, 0.7);', 'background: var(--bg-surface) !important; color: var(--text-primary) !important; border: 1px solid var(--border-color) !important;')
]
update_file('templates/alumni/events.html', events_replacements)

print("Alumni templates batch update completed.")
