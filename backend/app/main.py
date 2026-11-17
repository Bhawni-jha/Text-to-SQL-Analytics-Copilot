import logging
import time
from urllib.parse import urlparse
from contextlib import asynccontextmanager

import groq
import psycopg2
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .auth import current_user, hash_password, required_user, create_session, verify_password
from .dashboard import create_dashboard, delete_dashboard, init_dashboards, list_dashboards, update_dashboard
from .history import clear_history, delete_history, init_history, list_history, save_history
from .models import AskRequest, AskResponse, AuthRequest, ConnectionTestRequest, DashboardRequest, RunRequest
from .runner import QueryError, run_query
from .schema import get_schema, schema_for_ui
from .service import answer_question
from .validator import SQLValidationError, validate_sql

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_history()
    init_dashboards()
    yield


app = FastAPI(title="Text-to-SQL Analytics Copilot", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"status": "ok", "model": settings.groq_model}


@app.get("/api/schema")
def schema():
    try:
        return {"tables": schema_for_ui(get_schema())}
    except Exception as exc:
        raise HTTPException(500, f"Could not read the database schema: {exc}")


@app.post("/api/ask", response_model=AskResponse)
def ask(req: AskRequest, user_id: int | None = Depends(current_user)):
    question = req.question.strip()
    started = time.perf_counter()

    try:
        outcome = answer_question(question, req.tables)
    except groq.AuthenticationError:
        raise HTTPException(500, "The Groq API key is missing or invalid. Check GROQ_API_KEY in backend/.env")
    except groq.GroqError as exc:
        raise HTTPException(502, f"The language model request failed: {exc}")
    except Exception as exc:
        raise HTTPException(500, f"Something went wrong: {exc}")

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    history_id = save_history(
        question, outcome.sql, outcome.explanation, outcome.success,
        outcome.error, outcome.row_count, outcome.attempts, elapsed_ms, user_id,
    )
    return AskResponse(
        success=outcome.success, question=question, sql=outcome.sql,
        explanation=outcome.explanation, columns=outcome.columns, rows=outcome.rows,
        row_count=outcome.row_count, truncated=outcome.truncated, attempts=outcome.attempts,
        elapsed_ms=elapsed_ms, error=outcome.error, history_id=history_id,
    )


@app.post("/api/run", response_model=AskResponse)
def run_edited_sql(req: RunRequest, user_id: int | None = Depends(current_user)):
    """Runs SQL that the user edited by hand. It goes through the same safety checks."""
    started = time.perf_counter()
    question = "(edited SQL)"
    try:
        clean = validate_sql(req.sql)
        result = run_query(clean)
    except (SQLValidationError, QueryError) as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        history_id = save_history(question, req.sql, "", False, str(exc), 0, 1, elapsed_ms, user_id)
        return AskResponse(
            success=False, question=question, sql=req.sql, attempts=1,
            elapsed_ms=elapsed_ms, error=str(exc), history_id=history_id,
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    history_id = save_history(question, clean, "", True, None, result.row_count, 1, elapsed_ms, user_id)
    return AskResponse(
        success=True, question=question, sql=clean, columns=result.columns, rows=result.rows,
        row_count=result.row_count, truncated=result.truncated, attempts=1,
        elapsed_ms=elapsed_ms, history_id=history_id,
    )


@app.get("/api/history")
def history(limit: int = 20, user_id: int | None = Depends(current_user)):
    return {"items": list_history(max(1, min(limit, 100)), user_id)}


@app.delete("/api/history/{history_id}")
def remove_history(history_id: int, user_id: int | None = Depends(current_user)):
    if not delete_history(history_id, user_id):
        raise HTTPException(404, "History item not found")
    return {"ok": True}


@app.delete("/api/history")
def remove_all_history(user_id: int | None = Depends(current_user)):
    return {"deleted": clear_history(user_id)}


def _app_connection():
    if not settings.app_db_url:
        raise HTTPException(503, "App database is not configured")
    return psycopg2.connect(settings.app_db_url)


@app.post("/api/auth/register")
def register(req: AuthRequest):
    conn = _app_connection()
    try:
        with conn, conn.cursor() as cur:
            cur.execute("INSERT INTO users (email,password_hash) VALUES (%s,%s) RETURNING id", (req.email.strip().lower(), hash_password(req.password)))
            user_id = cur.fetchone()[0]
    except psycopg2.IntegrityError:
        raise HTTPException(409, "An account with that email already exists")
    finally:
        conn.close()
    return {"token": create_session(user_id), "user_id": user_id, "email": req.email.strip().lower()}


@app.post("/api/auth/login")
def login(req: AuthRequest):
    conn = _app_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id,password_hash FROM users WHERE email=%s", (req.email.strip().lower(),))
            row = cur.fetchone()
    finally:
        conn.close()
    if not row or not verify_password(req.password, row[1]):
        raise HTTPException(401, "Invalid email or password")
    return {"token": create_session(row[0]), "user_id": row[0], "email": req.email.strip().lower()}


@app.get("/api/auth/me")
def me(user_id: int = Depends(required_user)):
    conn = _app_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, email FROM users WHERE id=%s", (user_id,))
            row = cur.fetchone()
    finally:
        conn.close()
    if not row:
        raise HTTPException(401, "Account no longer exists")
    return {"user_id": row[0], "email": row[1]}


@app.get("/api/dashboards")
def dashboards(user_id: int = Depends(required_user)):
    return {"items": list_dashboards(user_id)}


@app.post("/api/dashboards")
def dashboard_create(req: DashboardRequest, user_id: int = Depends(required_user)):
    return {"id": create_dashboard(user_id, req)}


@app.put("/api/dashboards/{dashboard_id}")
def dashboard_update(dashboard_id: int, req: DashboardRequest, user_id: int = Depends(required_user)):
    if not update_dashboard(user_id, dashboard_id, req):
        raise HTTPException(404, "Dashboard not found")
    return {"ok": True}


@app.delete("/api/dashboards/{dashboard_id}")
def dashboard_delete(dashboard_id: int, user_id: int = Depends(required_user)):
    if not delete_dashboard(user_id, dashboard_id):
        raise HTTPException(404, "Dashboard not found")
    return {"ok": True}


@app.post("/api/connections/test")
def test_connection(req: ConnectionTestRequest, user_id: int = Depends(required_user)):
    parsed = urlparse(req.url)
    if parsed.scheme not in ("postgres", "postgresql") or not parsed.hostname:
        raise HTTPException(400, "Only a valid PostgreSQL URL is accepted")
    conn = None
    try:
        conn = psycopg2.connect(req.url, connect_timeout=5, options="-c statement_timeout=5000")
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            database = cur.fetchone()[0]
        return {"ok": True, "database": database}
    except psycopg2.Error as exc:
        # Do not echo the connection string: drivers or proxies may include it
        # (including credentials) in an exception message.
        message = getattr(getattr(exc, "diag", None), "message_primary", None)
        return {"ok": False, "error": message[:300] if message else "Connection failed"}
    finally:
        if conn:
            conn.close()
