import os
import sys
import re

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import app

with app.app_context():
    valid_endpoints = set(app.view_functions.keys())
    valid_endpoints.add('static')

    pattern = re.compile(r"url_for\(\s*['\"]([^'\"]+)['\"]")
    errors = []

    for root, dirs, files in os.walk('templates'):
        for f in files:
            if f.endswith('.html'):
                p = os.path.join(root, f)
                with open(p, 'r', encoding='utf-8') as fh:
                    content = fh.read()
                matches = pattern.findall(content)
                for m in matches:
                    if m not in valid_endpoints:
                        errors.append((p, m))

    if errors:
        print('INVALID url_for ENDPOINTS FOUND:')
        for path, ep in errors:
            print(f'  {path} -> {ep}')
    else:
        print('ALL url_for endpoints across ALL templates are 100% VALID!')
