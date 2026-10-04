"""SQLite helpers for the notes API.

Keeps all the SQL in one place so the routes stay thin. Uses stdlib
sqlite3 on purpose — the point of this project was to get comfortable
writing SQL by hand instead of leaning on an ORM.
"""

import sqlite3
import time

DB_PATH = "notes.db"


def get_db(path=DB_PATH):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(path=DB_PATH):
    """Create tables if they don't exist yet."""
    conn = get_db(path)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            body TEXT NOT NULL DEFAULT '',
            created_at REAL NOT NULL,
            updated_at REAL NOT NULL
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE IF NOT EXISTS note_tags (
            note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
            tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (note_id, tag_id)
        );
        """
    )
    conn.commit()
    conn.close()


def row_to_dict(row):
    """sqlite3.Row -> plain dict for jsonify."""
    return dict(row)


def now():
    return time.time()
