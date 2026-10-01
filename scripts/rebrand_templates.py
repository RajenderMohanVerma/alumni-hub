"""
Branding maintenance script for Alumni Hub.

Ensures the project branding stays as "Alumni Hub" across all templates.
Converts any leftover "DBIT Alumni Hub" / "DBIT ALUMNI HUB" occurrences
back to the neutral "Alumni Hub" / "ALUMNI HUB" branding.

Usage:
    python scripts/rebrand_templates.py
"""

import os

# Project root = parent of this script's directory
root_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates")

TEXT_EXTENSIONS = (".html", ".py", ".js", ".css", ".txt", ".md", ".json", ".xml")

updated = 0
for subdir, dirs, files in os.walk(root_dir):
    # Skip caches and user uploads
    dirs[:] = [d for d in dirs if d not in ("__pycache__", "uploads", "images")]
    for file in files:
        if not file.endswith(TEXT_EXTENSIONS):
            continue
        filepath = os.path.join(subdir, file)
        with open(filepath, "r", encoding="utf-8", errors="strict") as f:
            content = f.read()

        new_content = content.replace("DBIT ALUMNI HUB", "ALUMNI HUB")
        new_content = new_content.replace("DBIT Alumni Hub", "Alumni Hub")

        if content != new_content:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(new_content)
            print(f"Updated {filepath}")
            updated += 1

print(f"Done. {updated} file(s) updated.")
