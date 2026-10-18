import os
import jinja2

env = jinja2.Environment(loader=jinja2.FileSystemLoader('templates'))

# Register common dummy filters used in templates so jinja won't fail
env.filters['initials'] = lambda x: 'JD'
env.filters['timeago'] = lambda x: 'just now'

directories = ['student', 'alumni', 'faculty', 'admin', 'auth']
errors = 0

for d in directories:
    dir_path = os.path.join('templates', d)
    if not os.path.exists(dir_path):
        continue
    for f in os.listdir(dir_path):
        if f.endswith('.html'):
            rel_path = f"{d}/{f}"
            try:
                env.get_template(rel_path)
                print(f"[OK] {rel_path}")
            except Exception as e:
                print(f"[ERROR] {rel_path}: {e}")
                errors += 1

print(f"\nTotal errors: {errors}")
