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

# 1. Update templates/student/dashboard.html
dashboard_replacements = [
    ('style="background: rgba(255, 255, 255, 0.8);"', 'style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 18px;"'),
    ('style="border-radius: 20px; background: white; transition: all 0.3s ease;"', 'style="border-radius: 18px; background: var(--bg-surface); color: var(--text-primary); border: 1px solid var(--border-color); transition: all 0.3s ease;"'),
    ('style="background: rgba(255,255,255,0.5); border: 2px dashed #e0e7ff;"', 'style="background: var(--bg-surface); border: 2px dashed var(--border-color); border-radius: 18px;"'),
    ('style="background: rgba(255,255,255,0.8); backdrop-filter: blur(10px); border-radius: 18px; border: 1px solid #e0e7ff;"', 'style="background: var(--bg-surface); border-radius: 18px; border: 1px solid var(--border-color);"'),
    ('style="background: rgba(255,255,255,0.3); backdrop-filter: blur(20px);"', 'style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 18px;"'),
    ('style="background: white; border: 1px solid #e2e8f0; border-radius: 30px; border-left: 8px solid #667eea;"', 'style="background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 18px; border-left: 6px solid var(--accent-blue);"'),
    ('style="max-width: 900px; background: rgba(255, 255, 255, 0.6);"', 'style="max-width: 900px; background: var(--bg-surface); border: 1px solid var(--border-color); border-radius: 18px;"'),
    ('text-dark', 'text-theme-primary'),
    ('background-color: #f8fafc;', 'background-color: var(--bg-primary) !important; color: var(--text-primary) !important;'),
    ('background: #f8fafc;', 'background: var(--bg-primary);')
]

update_file('templates/student/dashboard.html', dashboard_replacements)

# 2. Update templates/student/profile.html
profile_replacements = [
    ('background-color: #f8fafc;', 'background-color: var(--bg-primary) !important; color: var(--text-primary) !important;'),
    ('background: #f8fafc;', 'background: var(--bg-primary);'),
    ('background: rgba(255, 255, 255, 0.7);', 'background: var(--bg-surface) !important; color: var(--text-primary) !important;'),
    ('background: rgba(255, 255, 255, 0.9);', 'background: var(--bg-surface) !important; color: var(--text-primary) !important;'),
    ('background: #fff;\n        border-radius: 20px;\n        padding: 1.5rem;\n        display: flex;\n        align-items: center;\n        gap: 1.5rem;\n        border: 1px solid #f1f5f9;', 'background: var(--bg-surface);\n        border-radius: 18px;\n        padding: 1.5rem;\n        display: flex;\n        align-items: center;\n        gap: 1.5rem;\n        border: 1px solid var(--border-color);'),
    ('background: #fff;\n        border-radius: 16px;\n        padding: 1rem 1.5rem;\n        display: flex;\n        align-items: center;\n        gap: 1.2rem;\n        border: 1px solid #f1f5f9;', 'background: var(--bg-surface);\n        border-radius: 16px;\n        padding: 1rem 1.5rem;\n        display: flex;\n        align-items: center;\n        gap: 1.2rem;\n        border: 1px solid var(--border-color);'),
    ('color: #1e293b;', 'color: var(--text-primary);')
]

update_file('templates/student/profile.html', profile_replacements)

# 3. Update templates/student/edit_profile.html
edit_profile_replacements = [
    ('background-color: #f8fafc;', 'background-color: var(--bg-primary) !important; color: var(--text-primary) !important;'),
    ('background: #f8fafc;', 'background: var(--bg-primary);'),
    ('background: rgba(255, 255, 255, 0.96);', 'background: var(--bg-surface) !important; color: var(--text-primary) !important; border-color: var(--border-color) !important;'),
    ('background: #fff;\n        transition: all 0.3s ease;', 'background: var(--input-bg);\n        color: var(--input-text);\n        border-color: var(--border-color);\n        transition: all 0.3s ease;'),
    ('color: #0f172a;', 'color: var(--text-primary);'),
    ('color: #475569;', 'color: var(--text-muted);'),
    ('background: rgba(255, 255, 255, 0.9);', 'background: var(--bg-surface); color: var(--text-primary);')
]

update_file('templates/student/edit_profile.html', edit_profile_replacements)

print("Student pages processing completed.")
