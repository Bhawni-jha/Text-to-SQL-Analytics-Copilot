from typing import Any

from pydantic import BaseModel, Field


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    tables: list[str] = Field(default_factory=list, max_length=50)


class RunRequest(BaseModel):
    sql: str = Field(min_length=1, max_length=5000)


class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=8, max_length=200)


class DashboardRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    question: str = Field(default="", max_length=500)
    sql: str = Field(default="", max_length=5000)
    config: dict = Field(default_factory=dict)


class ConnectionTestRequest(BaseModel):
    url: str = Field(min_length=12, max_length=2048)


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
