"""
Database access layer for Alumni Hub.

Every module in the project obtains its connection from get_db_connection()
rather than calling sqlite3.connect() directly, so this file is the single
place that decides which backend is in play:

  local SQLite  -> stdlib sqlite3, the original behaviour
  Turso Cloud   -> libsql over HTTP, wrapped in a compatibility shim

The shim exists because the libsql driver returns plain tuples and has no
row_factory support, while this project reads rows as row['column_name'] in
roughly a hundred places. Wrapping here keeps all of that code unchanged.
"""

import os
import sqlite3

from flask import current_app


class TursoDriverMissing(RuntimeError):
    """Raised when a Turso URL is configured but the driver is not installed."""


# ---------------------------------------------------------------------------
# Compatibility shim: sqlite3.Row semantics over the libsql driver
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Exception translation
# ---------------------------------------------------------------------------

# The libsql driver raises a plain ValueError for every SQL error, while
# stdlib sqlite3 raises OperationalError / IntegrityError / DatabaseError.
# This project has ten `except sqlite3.<Error>` handlers (schema migration,
# duplicate-email checks, etc.), so errors are translated back to the matching
# sqlite3 exception types as they cross the driver boundary.
_ERROR_CLASSES = (
    (('UNIQUE constraint failed', 'PRIMARY KEY constraint failed',
      'NOT NULL constraint failed', 'FOREIGN KEY constraint failed',
      'CHECK constraint failed', 'constraint failed'),
     sqlite3.IntegrityError),
    (('no such table', 'no such column', 'no such index', 'no such view',
      'duplicate column name', 'duplicate table name', 'syntax error',
      'incomplete input', 'misuse of', 'database is locked',
      'attempt to write a readonly', 'has no column named',
      'no such function', 'no such module', 'too many SQL variables'),
     sqlite3.OperationalError),
    (('cannot start a transaction within a transaction',
      'cannot rollback - no transaction is active'),
     sqlite3.OperationalError),
)


def translate_db_error(exc):
    """Re-raise a driver ValueError as the matching sqlite3 exception."""
    if isinstance(exc, sqlite3.Error):
        return exc

    message = str(exc)
    lowered = message.lower()
    for needles, exc_class in _ERROR_CLASSES:
        if any(n in lowered for n in needles):
            return exc_class(message)

    # Unrecognised SQL error: OperationalError is the closest safe match, since
    # callers that catch it treat it as "the database rejected this statement".
    return sqlite3.OperationalError(message)


class Row(dict):
    """
    A result row that behaves like sqlite3.Row.

    Supports both column-name access (row['name']) and positional access
    (row[0]), which is what stdlib sqlite3.Row allows, plus keys()/items()/
    values()/dict() for the messaging layer that converts rows to dicts.
    """

    __slots__ = ()

    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        if isinstance(key, slice):
            return list(self.values())[key]
        return dict.__getitem__(self, key)

    def __iter__(self):
        # sqlite3.Row iterates VALUES, not keys. Match that.
        return iter(self.values())

    def __repr__(self):
        return f"<Row {dict.__repr__(self)}>"


def _rows_from_description(description, raw_rows):
    """Convert libsql tuples into Row objects using the cursor description."""
    if not raw_rows:
        return []
    if not description:
        return [Row(enumerate(r)) for r in raw_rows]

    columns = [d[0] for d in description]
    return [Row(zip(columns, values)) for values in raw_rows]


class TursoCursor:
    """
    Wraps a libsql Cursor and restores sqlite3 semantics.

    Two driver quirks are corrected here, both of which the project depends on:

    1. Rows come back as plain tuples, so they are converted to Row objects
       using cursor.description.
    2. libsql reports cursor.rowcount correctly only for a freshly created
       cursor. Reusing one cursor across statements returns a stale value, so
       every execute() gets its own underlying cursor.
    3. libsql's fetchone() after fetchall() restarts from the first row instead
       of returning None, so results are buffered and served by this class.

    Result sets in this project are small (profile rows, message threads,
    recommendation candidates), so buffering them is not a concern.
    """

    def __init__(self, connection):
        self._connection = connection
        self._cursor = None
        self._rows = []
        self._position = 0
        self._description = None

    def execute(self, sql, parameters=None):
        # A new underlying cursor per statement keeps rowcount accurate.
        self._cursor = self._connection.cursor()
        try:
            if parameters is None:
                self._cursor.execute(sql)
            else:
                self._cursor.execute(sql, parameters)
        except Exception as exc:
            raise translate_db_error(exc) from exc

        self._description = self._cursor.description
        raw = self._cursor.fetchall()
        self._rows = _rows_from_description(self._description, raw)
        self._position = 0
        return self

    def executemany(self, sql, seq_of_parameters):
        self._cursor = self._connection.cursor()
        try:
            self._cursor.executemany(sql, seq_of_parameters)
        except Exception as exc:
            raise translate_db_error(exc) from exc
        self._description = self._cursor.description
        self._rows = []
        self._position = 0
        return self

    def executescript(self, sql_script):
        self._cursor = self._connection.cursor()
        try:
            self._cursor.executescript(sql_script)
        except Exception as exc:
            raise translate_db_error(exc) from exc
        self._description = None
        self._rows = []
        self._position = 0
        return self

    def fetchone(self):
        if self._position >= len(self._rows):
            return None
        row = self._rows[self._position]
        self._position += 1
        return row

    def fetchmany(self, size=None):
        if size is None:
            size = self.arraysize
        end = self._position + size
        chunk = self._rows[self._position:end]
        self._position = end
        return chunk

    def fetchall(self):
        remaining = self._rows[self._position:]
        self._position = len(self._rows)
        return remaining

    @property
    def description(self):
        return self._description

    @property
    def lastrowid(self):
        return self._cursor.lastrowid if self._cursor else None

    @property
    def rowcount(self):
        return self._cursor.rowcount if self._cursor else -1

    @property
    def arraysize(self):
        if self._cursor is not None:
            try:
                return self._cursor.arraysize
            except Exception:
                pass
        return 1

    def close(self):
        if self._cursor is not None:
            try:
                self._cursor.close()
            except Exception:
                pass
            self._cursor = None

    def __iter__(self):
        while True:
            row = self.fetchone()
            if row is None:
                return
            yield row

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


class TursoConnection:
    """
    Wraps a libsql Connection so it can stand in for a sqlite3.Connection.

    Only the surface this project actually uses is implemented. row_factory is
    accepted and ignored, because rows are already Row objects.
    """

    def __init__(self, connection):
        self._connection = connection
        self.row_factory = sqlite3.Row

    def cursor(self):
        return TursoCursor(self._connection)

    def execute(self, sql, parameters=None):
        cursor = self.cursor()
        cursor.execute(sql, parameters)
        return cursor

    def executemany(self, sql, seq_of_parameters):
        return self._connection.executemany(sql, seq_of_parameters)

    def executescript(self, sql_script):
        return self._connection.executescript(sql_script)

    def commit(self):
        return self._connection.commit()

    def rollback(self):
        return self._connection.rollback()

    def close(self):
        return self._connection.close()

    @property
    def description(self):
        return getattr(self._connection, 'description', None)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

def _turso_enabled():
    return bool(os.getenv('TURSO_DATABASE_URL'))


def _connect_turso():
    """
    Open a remote connection to Turso Cloud over HTTP.

    Turso hosts two incompatible engines and the wrong driver fails at connect
    time, so the engine is declared explicitly:

      TURSO_ENGINE=libsql   (default) — dashboard-created databases
      TURSO_ENGINE=tursodb  — the Turso engine, MVCC concurrent writes
    """
    url = os.getenv('TURSO_DATABASE_URL')
    token = os.getenv('TURSO_AUTH_TOKEN')
    engine = (os.getenv('TURSO_ENGINE') or 'libsql').strip().lower()

    if not token:
        raise TursoDriverMissing(
            "TURSO_DATABASE_URL is set but TURSO_AUTH_TOKEN is missing. "
            "Copy a token from the Turso dashboard."
        )

    if engine == 'tursodb':
        try:
            import turso_serverless as driver
        except ImportError as exc:
            raise TursoDriverMissing(
                "TURSO_ENGINE=tursodb requires the 'turso_serverless' package: "
                "pip install turso_serverless"
            ) from exc
    else:
        try:
            import libsql as driver
        except ImportError as exc:
            raise TursoDriverMissing(
                "Turso is configured but the 'libsql' package is not installed: "
                "pip install libsql"
            ) from exc

    return driver.connect(url, auth_token=token)


def get_db_connection():
    """
    Get a database connection using current_app config.
    Using current_app prevents circular imports with app.py.

    Two backends, chosen by the presence of TURSO_DATABASE_URL:

      Turso Cloud  -> remote HTTP connection wrapped in the Row shim
      local SQLite -> the original on-disk database

    Both expose cursor/execute/commit/close and return sqlite3.Row-style rows,
    so every call site in the project keeps working unchanged.
    """
    if _turso_enabled():
        return TursoConnection(_connect_turso())

    db_name = current_app.config.get('DB_NAME', 'data/alumni.db')
    conn = sqlite3.connect(db_name, timeout=20.0)
    # WAL only applies to a local file; it is meaningless over HTTP.
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.row_factory = sqlite3.Row
    return conn


def is_turso():
    """True when this process is talking to Turso Cloud rather than a local file."""
    return _turso_enabled()


def dump_to_sql(path):
    """
    Write a portable SQL dump of every user table to `path`.

    Used by the admin "download database" feature when running on Turso, where
    no local .db file exists to copy.
    """
    conn = get_db_connection()
    try:
        tables = [
            r[0]
            for r in conn.execute(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]

        with open(path, 'w', encoding='utf-8') as fh:
            fh.write("PRAGMA foreign_keys=OFF;\n")
            fh.write("BEGIN TRANSACTION;\n")

            for table in tables:
                fh.write(f"\n-- ---------- {table} ----------\n")
                create_sql = conn.execute(
                    "SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (table,)
                ).fetchone()
                if create_sql and create_sql[0]:
                    fh.write(create_sql[0].strip().rstrip(';') + ";\n")

                rows = conn.execute(f'SELECT * FROM "{table}"').fetchall()
                if not rows:
                    continue

                columns = rows[0].keys()
                col_list = ", ".join(f'"{c}"' for c in columns)
                for row in rows:
                    values = ", ".join(_sql_literal(row[c]) for c in columns)
                    fh.write(f'INSERT INTO "{table}" ({col_list}) VALUES ({values});\n')

            fh.write("\nCOMMIT;\n")
        return path
    finally:
        conn.close()


def _sql_literal(value):
    """Render a Python value as a SQL literal."""
    if value is None:
        return "NULL"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, bytes):
        return "X'" + value.hex() + "'"
    return "'" + str(value).replace("'", "''") + "'"