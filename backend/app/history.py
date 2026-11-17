"""Saves and lists past questions in the app database (copilot_app).

History is a nice-to-have: if the app database is down the copilot keeps working.
"""
import logging

import psycopg2

from .config import settings

log = logging.getLogger("history")

DDL = """
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS query_history (
    id          SERIAL PRIMARY KEY,
    question    TEXT        NOT NULL,
    sql         TEXT,
    explanation TEXT,
    success     BOOLEAN     NOT NULL,
    error       TEXT,
    row_count   INTEGER,
    attempts    INTEGER,
    elapsed_ms  INTEGER,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
)
"""


def _connect():
    return psycopg2.connect(settings.app_db_url)


def init_history() -> None:
    if not settings.app_db_url:
        log.warning("APP_DB_URL is not set: history is disabled.")
        return
    try:
        conn = _connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(DDL)
                cur.execute("ALTER TABLE query_history ADD COLUMN IF NOT EXISTS user_id INTEGER")
        finally:
            conn.close()
    except psycopg2.Error as exc:
        log.warning("History disabled (cannot reach app database): %s", exc)


def save_history(
    question: str,
    sql: str | None,
    explanation: str,
    success: bool,
    error: str | None,
    row_count: int,
    attempts: int,
    elapsed_ms: int,
    user_id: int | None = None,
) -> int | None:
    if not settings.app_db_url:
        return None
    try:
        conn = _connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    """INSERT INTO query_history
                       (question, sql, explanation, success, error, row_count, attempts, elapsed_ms, user_id)
                       VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                    (question, sql, explanation, success, error, row_count, attempts, elapsed_ms, user_id),
                )
                return cur.fetchone()[0]
        finally:
            conn.close()
    except psycopg2.Error as exc:
        log.warning("Could not save history: %s", exc)
        return None


def list_history(limit: int = 20, user_id: int | None = None) -> list[dict]:
    if not settings.app_db_url:
        return []
    try:
        conn = _connect()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """SELECT id, question, sql, success, row_count, created_at
                       FROM query_history
                       WHERE (user_id = %s OR (user_id IS NULL AND %s IS NULL))
                       ORDER BY id DESC LIMIT %s""",
                    (user_id, user_id, limit),
                )
                return [
                    {
                        "id": r[0],
                        "question": r[1],
                        "sql": r[2],
                        "success": r[3],
                        "row_count": r[4],
                        "created_at": r[5].isoformat(),
                    }
                    for r in cur.fetchall()
                ]
        finally:
            conn.close()
    except psycopg2.Error as exc:
        log.warning("Could not read history: %s", exc)
        return []


def delete_history(history_id: int, user_id: int | None = None) -> bool:
    if not settings.app_db_url:
        return False
    try:
        conn = _connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    """DELETE FROM query_history
                       WHERE id = %s
                       AND (user_id = %s OR (user_id IS NULL AND %s IS NULL))""",
                    (history_id, user_id, user_id),
                )
                return cur.rowcount > 0
        finally:
            conn.close()
    except psycopg2.Error as exc:
        log.warning("Could not delete history item: %s", exc)
        return False


def clear_history(user_id: int | None = None) -> int:
    if not settings.app_db_url:
        return 0
    try:
        conn = _connect()
        try:
            with conn, conn.cursor() as cur:
                cur.execute(
                    """DELETE FROM query_history
                       WHERE user_id = %s OR (user_id IS NULL AND %s IS NULL)""",
                    (user_id, user_id),
                )
                return cur.rowcount
        finally:
            conn.close()
    except psycopg2.Error as exc:
        log.warning("Could not clear history: %s", exc)
        return 0
