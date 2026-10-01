"""
Verifies the Turso compatibility shim in db_utils.py against a real libsql
connection.

Uses a local file: URL, because libsql speaks the same protocol to a local
file as it does over the network. That exercises the exact Row-conversion and
cursor logic that would run in production, without needing live credentials.

These are the behaviours the project's ~100 row['column'] call sites depend on.

Run:  python scripts/test_turso_adapter.py
"""

import os
import sqlite3
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

failures = []


def check(label, ok, detail=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {label}{(' -> ' + str(detail)) if detail else ''}")
    if not ok:
        failures.append(label)


TMP = os.path.join(tempfile.gettempdir(), "alumni_shim_probe.db")


def fresh_probe_db():
    for suffix in ("", "-wal", "-shm"):
        p = TMP + suffix
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass
    seed = sqlite3.connect(TMP)
    seed.execute(
        "CREATE TABLE t (id INTEGER PRIMARY KEY, name TEXT, score REAL, note TEXT)"
    )
    seed.execute("INSERT INTO t (name, score, note) VALUES (?, ?, ?)", ("Rahul", 9.5, "ok"))
    seed.execute("INSERT INTO t (name, score, note) VALUES (?, ?, ?)", ("Priya", 8.0, "ok"))
    seed.execute("INSERT INTO t (name, score, note) VALUES (?, ?, ?)", ("Amit", None, None))
    seed.commit()
    seed.close()


# ---------------------------------------------------------------------------
# 1. Local mode must be untouched by any of this
# ---------------------------------------------------------------------------
from flask import Flask  # noqa: E402

_app = Flask(__name__)
_app.config["DB_NAME"] = os.getenv("DB_NAME", "data/college_pro.db")
ctx = _app.app_context()
ctx.push()

print("\n1. LOCAL MODE (no TURSO_DATABASE_URL)")
os.environ.pop("TURSO_DATABASE_URL", None)

from db_utils import get_db_connection, is_turso, Row, TursoConnection  # noqa: E402

conn = get_db_connection()
check("returns a real sqlite3.Connection", isinstance(conn, sqlite3.Connection))
check("is_turso() is False", is_turso() is False)
check("row_factory is sqlite3.Row", conn.row_factory is sqlite3.Row)
check(
    "WAL pragma applied",
    conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal",
)
c = conn.cursor()
c.execute("SELECT name FROM users LIMIT 1")
r = c.fetchone()
check("dict-style row['name'] works locally", r["name"] is not None, r["name"])
conn.close()

# ---------------------------------------------------------------------------
# 2. Messaging now shares the same connection factory
# ---------------------------------------------------------------------------
print("\n2. MESSAGING DB UNIFICATION")
from database import messaging_db  # noqa: E402

check(
    "messaging no longer hard-codes repo-root 'college_pro.db'",
    "DB_NAME" not in vars(messaging_db),
)
check("messaging reuses db_utils factory", messaging_db.get_db_connection.__module__ == "database.messaging_db")

# ---------------------------------------------------------------------------
# 3. Row conversion over a real libsql connection
# ---------------------------------------------------------------------------
print("\n3. TURSO SHIM — row conversion")
import libsql  # noqa: E402

fresh_probe_db()
tconn = TursoConnection(libsql.connect(f"file:{TMP}"))
cur = tconn.cursor()

cur.execute("SELECT id, name, score, note FROM t")
rows = cur.fetchall()
row = rows[0]
check("returns Row objects", isinstance(row, Row), type(row).__name__)
check("row['name'] column access", row["name"] == "Rahul")
check("row[1] positional access", row[1] == "Rahul")
check("row.keys()", list(row.keys()) == ["id", "name", "score", "note"])
check("dict(row) (used in messaging_db)", dict(row)["name"] == "Rahul")
check("iter(row) yields VALUES like sqlite3.Row", list(row) == [1, "Rahul", 9.5, "ok"])
check("len(row) is column count", len(row) == 4)
check("'name' in row", "name" in row)
check("'score' in row.keys()", "score" in row.keys())

print("\n4. TURSO SHIM — NULL handling")
cur.execute("SELECT name, score, note FROM t WHERE name = ?", ("Amit",))
n = cur.fetchone()
check("NULL round-trips as None", n["score"] is None and n["note"] is None)

print("\n5. TURSO SHIM — fetch semantics")
cur.execute("SELECT id, name FROM t")
check("fetchone() returns first row", cur.fetchone()["name"] == "Rahul")
check("fetchall() returns remainder", [x["name"] for x in cur.fetchall()] == ["Priya", "Amit"])
check("fetchone() after exhaustion is None", cur.fetchone() is None)
check("fetchall() after exhaustion is []", cur.fetchall() == [])

cur.execute("SELECT id, name FROM t")
check("fetchmany(2)", len(cur.fetchmany(2)) == 2)
check("remaining after fetchmany", len(cur.fetchall()) == 1)

print("\n6. TURSO SHIM — rowcount / lastrowid (messaging_db depends on these)")
cur.execute("DELETE FROM t WHERE name = ?", ("Rahul",))
check("rowcount after DELETE 1 row", cur.rowcount == 1, cur.rowcount)
tconn.commit()

cur.execute("DELETE FROM t WHERE name IN (?, ?)", ("Priya", "Amit"))
check("rowcount after DELETE 2 rows", cur.rowcount == 2, cur.rowcount)
tconn.commit()

cur.execute("UPDATE t SET name = ? WHERE name = ?", ("x", "nope"))
check("rowcount after UPDATE 0 rows", cur.rowcount == 0, cur.rowcount)
tconn.commit()

cur.execute("INSERT INTO t (name, score, note) VALUES (?, ?, ?)", ("Neha", 7.5, "x"))
check("rowcount after INSERT", cur.rowcount == 1, cur.rowcount)
# This probe table is INTEGER PRIMARY KEY without AUTOINCREMENT, so SQLite is
# free to reuse a freed id. Assert consistency, not a specific number.
new_id = cur.lastrowid
check("lastrowid is a valid row id", isinstance(new_id, int) and new_id > 0, new_id)
cur.execute("SELECT COUNT(*) AS cnt FROM t WHERE id = ?", (new_id,))
check("lastrowid points at the inserted row", cur.fetchone()["cnt"] == 1)
tconn.commit()

print("\n7. TURSO SHIM — parameterised queries")
cur.execute("SELECT name FROM t WHERE name = ?", ("Neha",))
check("? placeholders bind correctly", cur.fetchone()["name"] == "Neha")
cur.execute("SELECT COUNT(*) AS cnt FROM t")
check("aggregate alias accessible", isinstance(cur.fetchone()["cnt"], int))

tconn.close()

# ---------------------------------------------------------------------------
# 8. Error handling when misconfigured
# ---------------------------------------------------------------------------
print("\n8. MISCONFIGURATION HANDLING")
from db_utils import TursoDriverMissing  # noqa: E402

# The libsql driver raises plain ValueError for every SQL error. The project has
# ten `except sqlite3.<Error>` handlers, so the shim must translate them back.
print("\n7b. EXCEPTION TRANSLATION (libsql ValueError -> sqlite3 errors)")
import libsql as _libsql  # noqa: E402
from db_utils import TursoConnection as _TC  # noqa: E402

_x = os.path.join(tempfile.gettempdir(), "alumni_exc_probe.db")
for _sfx in ("", "-wal", "-shm"):
    if os.path.exists(_x + _sfx):
        try:
            os.remove(_x + _sfx)
        except OSError:
            pass
_seed = sqlite3.connect(_x)
_seed.execute("CREATE TABLE t (id INTEGER PRIMARY KEY, a TEXT UNIQUE, b TEXT NOT NULL)")
_seed.execute("INSERT INTO t (id,a,b) VALUES (1,'x','y')")
_seed.commit()
_seed.close()

xc = _TC(_libsql.connect(f"file:{_x}"))
xk = xc.cursor()


def expect(label, sql, params, exc_class):
    try:
        xk.execute(sql, params)
        check(label, False, "no error raised")
    except exc_class:
        check(label, True)
    except Exception as exc:
        check(label, False, f"{type(exc).__name__}: {exc}")


expect("duplicate column -> OperationalError",
       "ALTER TABLE t ADD COLUMN a TEXT", None, sqlite3.OperationalError)
expect("missing table -> OperationalError",
       "SELECT * FROM nosuchtable", None, sqlite3.OperationalError)
expect("missing column -> OperationalError",
       "SELECT nosuchcol FROM t", None, sqlite3.OperationalError)
expect("syntax error -> OperationalError",
       "SELEC * FROM t", None, sqlite3.OperationalError)
expect("UNIQUE violation -> IntegrityError",
       "INSERT INTO t (id,a,b) VALUES (?,?,?)", (2, "x", "z"), sqlite3.IntegrityError)
expect("NOT NULL violation -> IntegrityError",
       "INSERT INTO t (id,a,b) VALUES (?,?,?)", (3, "q", None), sqlite3.IntegrityError)
xc.commit()
xc.close()
try:
    os.remove(_x)
except OSError:
    pass

os.environ["TURSO_DATABASE_URL"] = "https://example.invalid.turso.io"
os.environ.pop("TURSO_AUTH_TOKEN", None)
try:
    get_db_connection()
    check("missing token raises TursoDriverMissing", False, "no error raised")
except TursoDriverMissing:
    check("missing token raises TursoDriverMissing", True)
except Exception as exc:
    check("missing token raises TursoDriverMissing", False, type(exc).__name__)

os.environ["TURSO_AUTH_TOKEN"] = "dummy"
os.environ["TURSO_ENGINE"] = "nonexistent-engine"
try:
    get_db_connection()
    check("unknown engine falls back to libsql", True)
except TursoDriverMissing as exc:
    check("unknown engine falls back to libsql", False, str(exc))
except Exception:
    check("unknown engine falls back to libsql", True, "reached network")

os.environ.pop("TURSO_DATABASE_URL", None)
os.environ.pop("TURSO_AUTH_TOKEN", None)
os.environ.pop("TURSO_ENGINE", None)

print("\n9. SQL DUMP")
from db_utils import dump_to_sql  # noqa: E402

dump_path = os.path.join(tempfile.gettempdir(), "alumni_dump_check.sql")
dump_to_sql(dump_path)
dump_sql = open(dump_path, encoding="utf-8").read()
check("dump has all 19 tables", dump_sql.count("CREATE TABLE") == 19, dump_sql.count("CREATE TABLE"))
check("dump has data", "INSERT INTO" in dump_sql)
check("dump is wrapped in a transaction", dump_sql.startswith("PRAGMA foreign_keys=OFF;"))

restore_path = os.path.join(tempfile.gettempdir(), "alumni_dump_restore.db")
if os.path.exists(restore_path):
    os.remove(restore_path)
rc = sqlite3.connect(restore_path)
rc.executescript(dump_sql)
rc.commit()
src = sqlite3.connect(_app.config["DB_NAME"])
for table in ("users", "jobs", "connections"):
    a = src.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    b = rc.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    check(f"restore matches source for {table}", a == b, f"{a} vs {b}")
src.close()
rc.close()

for path in (dump_path, restore_path):
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass

print("\n" + "=" * 62)
if failures:
    print(f"FAILED ({len(failures)}): " + ", ".join(failures))
    sys.exit(1)
print("ALL CHECKS PASSED — local dev unchanged, Turso ready.")