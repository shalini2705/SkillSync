"""
Database connection and utility functions for SQLite.
Provides connection pooling, row dict helpers, and transaction support.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

# Default database path
DEFAULT_DB_PATH = Path(__file__).resolve().parent / "course_recommender.db"


def get_db_path(custom_path: str = None) -> Path:
    """Returns the resolved database path from argument, environment variable, or default."""
    if custom_path:
        return Path(custom_path)
    env_path = os.getenv("DATABASE_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_DB_PATH


def get_connection(db_path: str = None) -> sqlite3.Connection:
    """
    Creates and returns a SQLite database connection with row factory set to sqlite3.Row
    and foreign key constraints enforced.
    """
    path = get_db_path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


@contextmanager
def get_db_cursor(db_path: str = None, commit: bool = True):
    """
    Context manager for database transactions.
    Automatically commits on success or rolls back on exception.
    """
    conn = get_connection(db_path)
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cursor.close()
        conn.close()


def init_db(db_path: str = None) -> None:
    """Initializes the database schema from schema.sql."""
    schema_path = Path(__file__).resolve().parent / "schema.sql"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at: {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema_sql = f.read()

    with get_db_cursor(db_path, commit=True) as cursor:
        cursor.executescript(schema_sql)


def fetch_one(query: str, params: tuple = (), db_path: str = None) -> dict:
    """Executes a SELECT query and returns a single row as a dictionary, or None."""
    with get_db_cursor(db_path, commit=False) as cursor:
        cursor.execute(query, params)
        row = cursor.fetchone()
        return dict(row) if row else None


def fetch_all(query: str, params: tuple = (), db_path: str = None) -> list:
    """Executes a SELECT query and returns all matching rows as dictionaries."""
    with get_db_cursor(db_path, commit=False) as cursor:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        return [dict(row) for row in rows]


def execute_query(query: str, params: tuple = (), db_path: str = None) -> int:
    """Executes an INSERT/UPDATE/DELETE query and returns the number of rows affected."""
    with get_db_cursor(db_path, commit=True) as cursor:
        cursor.execute(query, params)
        return cursor.rowcount


def execute_insert(query: str, params: tuple = (), db_path: str = None) -> int:
    """Executes an INSERT query and returns the auto-incremented primary key ID."""
    with get_db_cursor(db_path, commit=True) as cursor:
        cursor.execute(query, params)
        return cursor.lastrowid
