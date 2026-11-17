import json
import logging
import psycopg2

from .config import settings

log = logging.getLogger("dashboard")

DDL = """CREATE TABLE IF NOT EXISTS saved_dashboards (
 id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL, name TEXT NOT NULL,
 question TEXT NOT NULL DEFAULT '', sql TEXT NOT NULL DEFAULT '',
 config JSONB NOT NULL DEFAULT '{}'::jsonb,
 created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
 updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
)"""


def init_dashboards():
    if not settings.app_db_url:
        return
    try:
        conn = psycopg2.connect(settings.app_db_url)
        with conn, conn.cursor() as cur:
            cur.execute(DDL)
    except psycopg2.Error as exc:
        log.warning("Dashboards disabled: %s", exc)
    finally:
        if "conn" in locals():
            conn.close()


def _row(row):
    return {"id": row[0], "name": row[1], "question": row[2], "sql": row[3],
            "config": row[4] if isinstance(row[4], dict) else json.loads(row[4]),
            "created_at": row[5].isoformat(), "updated_at": row[6].isoformat()}


def list_dashboards(user_id):
    conn = psycopg2.connect(settings.app_db_url)
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id,name,question,sql,config,created_at,updated_at FROM saved_dashboards WHERE user_id=%s ORDER BY updated_at DESC", (user_id,))
            return [_row(r) for r in cur.fetchall()]
    finally:
        conn.close()


def create_dashboard(user_id, data):
    conn = psycopg2.connect(settings.app_db_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("INSERT INTO saved_dashboards (user_id,name,question,sql,config) VALUES (%s,%s,%s,%s,%s) RETURNING id", (user_id, data.name, data.question, data.sql, json.dumps(data.config)))
            return cur.fetchone()[0]
    finally:
        conn.close()


def update_dashboard(user_id, dashboard_id, data):
    conn = psycopg2.connect(settings.app_db_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("UPDATE saved_dashboards SET name=%s,question=%s,sql=%s,config=%s,updated_at=now() WHERE id=%s AND user_id=%s", (data.name, data.question, data.sql, json.dumps(data.config), dashboard_id, user_id))
            return cur.rowcount > 0
    finally:
        conn.close()


def delete_dashboard(user_id, dashboard_id):
    conn = psycopg2.connect(settings.app_db_url)
    try:
        with conn, conn.cursor() as cur:
            cur.execute("DELETE FROM saved_dashboards WHERE id=%s AND user_id=%s", (dashboard_id, user_id))
            return cur.rowcount > 0
    finally:
        conn.close()
