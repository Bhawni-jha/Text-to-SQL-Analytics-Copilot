import logging
import time
from contextlib import asynccontextmanager

import groq
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .history import init_history, list_history, save_history
from .models import AskRequest, AskResponse, RunRequest
from .runner import QueryError, run_query
from .schema import get_schema, schema_for_ui
from .service import answer_question
from .validator import SQLValidationError, validate_sql

logging.basicConfig(level=logging.INFO)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_history()
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
def ask(req: AskRequest):
    question = req.question.strip()
    started = time.perf_counter()

    try:
        outcome = answer_question(question)
    except groq.AuthenticationError:
        raise HTTPException(500, "The Groq API key is missing or invalid. Check GROQ_API_KEY in backend/.env")
    except groq.GroqError as exc:
        raise HTTPException(502, f"The language model request failed: {exc}")
    except Exception as exc:
        raise HTTPException(500, f"Something went wrong: {exc}")

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    history_id = save_history(
        question, outcome.sql, outcome.explanation, outcome.success,
        outcome.error, outcome.row_count, outcome.attempts, elapsed_ms,
    )
    return AskResponse(
        success=outcome.success, question=question, sql=outcome.sql,
        explanation=outcome.explanation, columns=outcome.columns, rows=outcome.rows,
        row_count=outcome.row_count, truncated=outcome.truncated, attempts=outcome.attempts,
        elapsed_ms=elapsed_ms, error=outcome.error, history_id=history_id,
    )


@app.post("/api/run", response_model=AskResponse)
def run_edited_sql(req: RunRequest):
    """Runs SQL that the user edited by hand. It goes through the same safety checks."""
    started = time.perf_counter()
    question = "(edited SQL)"
    try:
        clean = validate_sql(req.sql)
        result = run_query(clean)
    except (SQLValidationError, QueryError) as exc:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        history_id = save_history(question, req.sql, "", False, str(exc), 0, 1, elapsed_ms)
        return AskResponse(
            success=False, question=question, sql=req.sql, attempts=1,
            elapsed_ms=elapsed_ms, error=str(exc), history_id=history_id,
        )

    elapsed_ms = int((time.perf_counter() - started) * 1000)
    history_id = save_history(question, clean, "", True, None, result.row_count, 1, elapsed_ms)
    return AskResponse(
        success=True, question=question, sql=clean, columns=result.columns, rows=result.rows,
        row_count=result.row_count, truncated=result.truncated, attempts=1,
        elapsed_ms=elapsed_ms, history_id=history_id,
    )


@app.get("/api/history")
def history(limit: int = 20):
    return {"items": list_history(max(1, min(limit, 100)))}
