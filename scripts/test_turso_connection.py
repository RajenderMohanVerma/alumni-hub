"""
Check the Turso Cloud connection for Alumni Hub.

Reads TURSO_DATABASE_URL and TURSO_AUTH_TOKEN from .env, connects, and reports
what it found. Safe to run any time — it never writes to the database.

Run:  python scripts/test_turso_connection.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))


def fail(message, hint=""):
    print(f"\n  X  {message}")
    if hint:
        print(f"     {hint}")
    sys.exit(1)


url = os.getenv("TURSO_DATABASE_URL")
token = os.getenv("TURSO_AUTH_TOKEN")
engine = (os.getenv("TURSO_ENGINE") or "libsql").strip().lower()

print("=" * 62)
print("  ALUMNI HUB - TURSO CONNECTION CHECK")
print("=" * 62)
print(f"  URL      : {url or '(not set)'}")
print(f"  Token    : {'set' if token else 'EMPTY'}")
print(f"  Engine   : {engine}")
print()

if not url:
    fail(
        "TURSO_DATABASE_URL is not set",
        "Add it to .env. Copy it from the Turso dashboard.",
    )

if not token:
    print("  ->  Probing without a token to confirm the database is reachable...")
    reachable = False
    try:
        import libsql

        conn = libsql.connect(url, auth_token="")
        try:
            conn.cursor().execute("SELECT 1")
            reachable = True          # public database, no token needed
        except Exception as exc:
            text = str(exc).lower()
            # 401 means the server answered, so the database exists and is
            # reachable; it is only refusing us for want of a token.
            if "401" in text or "unauthorized" in text or "jwt" in text:
                reachable = True
                print("     Server responded (auth required) -> database IS reachable.")
            else:
                print(f"     Server error: {exc}")
    except ImportError:
        fail("The 'libsql' package is not installed", "Run: pip install libsql")
    except Exception as exc:
        print(f"  X  Network/DNS problem: {exc}")
        print("     Check your internet connection and the URL.")
        sys.exit(1)

    if not reachable:
        fail("Could not reach the database", "Verify TURSO_DATABASE_URL in .env.")

    print()
    fail(
        "TURSO_AUTH_TOKEN is empty",
        "Create a token in the Turso dashboard, paste it into .env, then run this again.",
    )

print("  ->  Connecting with the token...\n")

try:
    if engine == "tursodb":
        import turso_serverless
        _driver_connect = lambda u, t: turso_serverless.connect(u, auth_token=t)
    else:
        import libsql
        _driver_connect = lambda u, t: libsql.connect(u, auth_token=t)
except ImportError as exc:
    fail(
        f"Driver '{engine}' is not installed",
        f"Run: pip install {engine if engine == 'tursodb' else 'libsql'}",
    )

# Wrap in the same shim the app uses, so this script exercises the real path
# (rows behave like sqlite3.Row rather than raw tuples).
try:
    from db_utils import TursoConnection
except ImportError:
    fail("Could not import db_utils", "Run this script from the project root.")

try:
    conn = TursoConnection(_driver_connect(url, token))
    cursor = conn.cursor()
    cursor.execute("SELECT 1 AS ok")
    row = cursor.fetchone()
except Exception as exc:
    message = str(exc).lower()
    if "401" in message or "unauthorized" in message or "jwt" in message:
        fail(
            "Token was rejected (401 Unauthorized)",
            "The token is wrong or revoked. Create a new one in the dashboard.",
        )
    if "not found" in message or "404" in message:
        fail("Database URL not found", "Check TURSO_DATABASE_URL in .env.")
    fail(f"Connection failed: {exc}")

# The shim returns Row objects, so row['ok'] works exactly as it does in the app.
value = row["ok"] if not isinstance(row, (int, str)) else row
print(f"  [OK] Connected.  SELECT 1 returned {value}")

try:
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' "
        "AND name NOT LIKE 'sqlite_%' ORDER BY name"
    )
    tables = [r["name"] for r in cursor.fetchall()]
except Exception as exc:
    print(f"  [!!] Connected, but could not read the schema: {exc}")
    tables = []

if tables:
    print(f"  [OK] {len(tables)} table(s) present:")
    for name in tables:
        print(f"        - {name}")
else:
    print("  [--] The database is EMPTY (no tables yet).")
    print("       That is fine — the app creates its schema automatically on first boot.")

# Write permissions matter more than reads for this project.
try:
    cursor.execute("CREATE TABLE IF NOT EXISTS _turso_probe (id INTEGER PRIMARY KEY, ts TEXT)")
    cursor.execute(
        "INSERT INTO _turso_probe (ts) VALUES (datetime('now'))"
    )
    conn.commit()
    cursor.execute("SELECT COUNT(*) AS c FROM _turso_probe")
    n = cursor.fetchone()["c"]
    cursor.execute("DELETE FROM _turso_probe")
    conn.commit()
    print(f"  [OK] Write access confirmed (inserted and removed a probe row)")
except Exception as exc:
    print(f"  [!!] Read-only token, or writes are blocked: {exc}")

conn.close()

print()
print("=" * 62)
print("  CONNECTION OK - run:  python app.py")
print("=" * 62)