"""
The SQLite database for ADHAV AI.
SQLite keeps everything in ONE file (data/adhav.db). Nothing to install.
"""

import sqlite3
from contextlib import contextmanager

from backend import config

# Where the database file lives. (*.db is already listed in .gitignore.)
DB_PATH = config.PROJECT_ROOT / "data" / "adhav.db"


def get_connection() -> sqlite3.Connection:
    """Open the database file (it is created automatically if it does not exist)."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # lets us read columns by name
    return conn


@contextmanager
def connection():
    """
    Use it like:  with connection() as conn: ...
    It saves your changes when the block finishes, undoes them if an error
    happens, and always closes the connection.
    """
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create the tables if they do not exist yet. Safe to run many times."""
    with connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS memories (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id    TEXT NOT NULL DEFAULT 'local',
                memory     TEXT NOT NULL,
                category   TEXT NOT NULL DEFAULT 'other',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS settings (
                user_id TEXT NOT NULL,
                key     TEXT NOT NULL,
                value   TEXT NOT NULL,
                PRIMARY KEY (user_id, key)
            )
            """
        )