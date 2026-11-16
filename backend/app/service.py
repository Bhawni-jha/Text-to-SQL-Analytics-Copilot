"""The core flow, shared by the API and the evaluation script."""
from dataclasses import dataclass, field
from typing import Any

from .config import settings
from .llm import generate_sql
from .runner import QueryError, run_query
from .schema import get_schema, schema_to_text
from .validator import SQLValidationError, validate_sql


@dataclass
class Outcome:
    success: bool
    sql: str | None
    explanation: str
    columns: list[str] = field(default_factory=list)
    rows: list[list[Any]] = field(default_factory=list)
    row_count: int = 0
    truncated: bool = False
    attempts: int = 0
    error: str | None = None


def answer_question(question: str) -> Outcome:
    """question -> SQL -> validate -> run. On failure, retry once with the error message."""
    schema_text = schema_to_text(get_schema())
    last_sql: str | None = None
    error: str | None = None
    explanation = ""

    for attempt in range(1, settings.max_attempts + 1):
        generation = generate_sql(question, schema_text, last_sql, error)
        explanation = generation.explanation

        if generation.sql is None:
            return Outcome(
                False, None, explanation, attempts=attempt,
                error=explanation or "This question can't be answered from the database.",
            )

        last_sql = generation.sql
        try:
            clean = validate_sql(generation.sql)
            result = run_query(clean)
        except (SQLValidationError, QueryError) as exc:
            error = str(exc)
            continue

        return Outcome(
            True, clean, explanation, result.columns, result.rows,
            result.row_count, result.truncated, attempt,
        )

    return Outcome(False, last_sql, explanation, attempts=settings.max_attempts, error=error)
