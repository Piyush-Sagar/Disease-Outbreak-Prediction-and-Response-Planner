"""Database connection dependency for FastAPI endpoints."""

import sqlite3

from fastapi import HTTPException

from . import database
from .services.deps import ensure_ready


def get_db():
    ensure_ready()
    conn = database.get_connection()
    try:
        yield conn
    except sqlite3.Error as exc:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {exc}") from exc
    finally:
        conn.close()