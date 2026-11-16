"""Checks that generated SQL is a single, read-only SELECT before it is run.

This is the second safety layer. The first is the read-only database user and the
third is the read-only transaction + timeout set in runner.py.
"""
import re

import sqlglot
from sqlglot import exp


class SQLValidationError(Exception):
    pass


def _classes(names: list[str]) -> tuple:
    # getattr keeps this working across sqlglot versions that name classes differently
    return tuple(getattr(exp, name) for name in names if hasattr(exp, name))


ALLOWED_TOP_LEVEL = _classes(["Select", "Union", "Except", "Intersect", "SetOperation", "Subquery"])

FORBIDDEN_NODES = _classes(
    [
        "Insert", "Update", "Delete", "Drop", "Create", "Alter", "AlterTable", "Command",
        "Merge", "Copy", "TruncateTable", "Grant", "Revoke", "Set", "Use", "Into", "Lock",
        "Pragma", "Transaction", "Commit", "Rollback", "Analyze", "Execute", "Call", "Declare",
    ]
)

# Functions and objects that can read files, sleep, or reach other servers
DENYLIST = re.compile(
    r"\b(pg_sleep|pg_read_file|pg_read_binary_file|pg_ls_dir|pg_stat_file|lo_import|lo_export|"
    r"dblink|dblink_exec|set_config|pg_terminate_backend|pg_cancel_backend|pg_reload_conf|"
    r"pg_shadow|pg_authid)\b",
    re.IGNORECASE,
)

MAX_SQL_LENGTH = 5000


def validate_sql(sql: str) -> str:
    """Returns the cleaned SQL (no trailing semicolon) or raises SQLValidationError."""
    if not sql or not sql.strip():
        raise SQLValidationError("The query is empty.")

    clean = sql.strip()
    while clean.endswith(";"):
        clean = clean[:-1].rstrip()
    if not clean:
        raise SQLValidationError("The query is empty.")
    if len(clean) > MAX_SQL_LENGTH:
        raise SQLValidationError("The query is too long.")

    try:
        statements = [s for s in sqlglot.parse(clean, read="postgres") if s is not None]
    except Exception as exc:  # fail closed: anything we cannot parse is rejected
        raise SQLValidationError(f"The SQL could not be parsed: {exc}") from exc

    if len(statements) != 1:
        raise SQLValidationError("Only one SQL statement is allowed.")

    tree = statements[0]
    if not isinstance(tree, ALLOWED_TOP_LEVEL):
        raise SQLValidationError("Only SELECT queries are allowed.")

    bad = tree.find(*FORBIDDEN_NODES) if FORBIDDEN_NODES else None
    if bad is not None:
        raise SQLValidationError(f"Not allowed in a read-only query: {type(bad).__name__.upper()}.")

    match = DENYLIST.search(clean)
    if match:
        raise SQLValidationError(f"The function or object '{match.group(0)}' is not allowed.")

    return clean
