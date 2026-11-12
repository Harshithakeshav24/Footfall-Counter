import os
import sqlite3
from datetime import datetime

from app import config


def get_connection():
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    folder = os.path.dirname(config.DB_PATH)
    if folder:
        os.makedirs(folder, exist_ok=True)

    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS footfall_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            direction TEXT NOT NULL,
            entered INTEGER NOT NULL,
            exited INTEGER NOT NULL,
            total_count INTEGER NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_event(direction, entered, exited, total_count):
    """Save one line crossing together with the counts after it."""
    conn = get_connection()
    conn.execute(
        "INSERT INTO footfall_log (timestamp, direction, entered, exited, total_count) "
        "VALUES (?, ?, ?, ?, ?)",
        (datetime.now().isoformat(timespec="seconds"), direction, entered, exited, total_count),
    )
    conn.commit()
    conn.close()


def get_history(limit=20):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM footfall_log ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]
