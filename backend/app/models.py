from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


class RunRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=5000)


class AskResponse(BaseModel):
    success: bool
    question: str
    sql: str | None = None
    explanation: str = ""
    columns: list[str] = []
    rows: list[list[Any]] = []
    row_count: int = 0
    truncated: bool = False
    attempts: int = 0
    elapsed_ms: int = 0
    error: str | None = None
    history_id: int | None = None
