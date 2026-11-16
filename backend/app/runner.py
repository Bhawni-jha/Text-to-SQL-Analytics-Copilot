"""Runs a validated SELECT safely: read-only session, timeout and row limit."""
import datetime
import decimal
import time
import uuid
from dataclasses import dataclass
from typing import Any

import psycopg2

from .config import settings


class QueryError(Exception):
    pass


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[list[Any]]
    row_count: int
    truncated: bool
    elapsed_ms: int


def _jsonable(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, decimal.Decimal):
        return float(value)
    if isinstance(value, (datetime.datetime, datetime.date, datetime.time)):
        return value.isoformat()
    if isinstance(value, datetime.timedelta):
        return str(value)
    if isinstance(value, (uuid.UUID, memoryview, bytes)):
        return str(value)
    return str(value)


def run_query(sql: str, max_rows: int | None = None) -> QueryResult:
    limit = max_rows or settings.max_rows
    # The wrapper enforces the row limit even if the query has no LIMIT.
    # The newlines keep a trailing "-- comment" in the query from eating the wrapper.
    wrapped = f"SELECT * FROM (\n{sql}\n) AS _q LIMIT {int(limit) + 1}"

    conn = None
    try:
        conn = psycopg2.connect(
            settings.sample_db_url,
            options=(
                f"-c statement_timeout={settings.timeout_seconds * 1000} "
                "-c default_transaction_read_only=on"
            ),
        )
        conn.set_session(readonly=True)
        started = time.perf_counter()
        with conn.cursor() as cur:
            cur.execute(wrapped)
            columns = [d.name for d in cur.description]
            fetched = cur.fetchall()
        elapsed_ms = int((time.perf_counter() - started) * 1000)
    except psycopg2.Error as exc:
        message = (exc.pgerror or str(exc)).strip().splitlines()
        raise QueryError(message[0] if message else "Database error") from exc
    finally:
        if conn is not None:
            conn.close()

    truncated = len(fetched) > limit
    rows = [[_jsonable(v) for v in row] for row in fetched[:limit]]
    return QueryResult(columns, rows, len(rows), truncated, elapsed_ms)
