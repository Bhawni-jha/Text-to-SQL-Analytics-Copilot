"""Reads the table/column/key structure of the sample database."""
import logging
from functools import lru_cache

import psycopg2

from .config import settings

log = logging.getLogger("schema")

_TYPE_NAMES = {
    "character varying": "varchar",
    "character": "char",
    "timestamp without time zone": "timestamp",
    "timestamp with time zone": "timestamptz",
    "double precision": "float8",
    "integer": "int",
    "smallint": "smallint",
    "boolean": "bool",
}

COLUMNS_SQL = """
SELECT c.table_name, c.column_name, c.data_type
FROM information_schema.columns c
JOIN information_schema.tables t
  ON t.table_schema = c.table_schema AND t.table_name = c.table_name
WHERE c.table_schema = 'public' AND t.table_type = 'BASE TABLE'
ORDER BY c.table_name, c.ordinal_position
"""

# pg_catalog is used (not information_schema) because information_schema hides
# key constraints from users that only have SELECT permission.
KEYS_SQL = """
SELECT ct.relname AS table_name,
       a.attname  AS column_name,
       c.contype  AS kind,
       cf.relname AS ref_table,
       af.attname AS ref_column
FROM pg_constraint c
JOIN pg_namespace n ON n.oid = c.connamespace
JOIN pg_class ct ON ct.oid = c.conrelid
LEFT JOIN pg_class cf ON cf.oid = c.confrelid
CROSS JOIN LATERAL unnest(c.conkey, COALESCE(c.confkey, c.conkey)) AS k(attnum, fattnum)
JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum
LEFT JOIN pg_attribute af ON af.attrelid = c.confrelid AND af.attnum = k.fattnum
WHERE n.nspname = 'public' AND c.contype IN ('p', 'f')
"""


@lru_cache(maxsize=1)
def get_schema() -> dict:
    """Returns {"tables": {name: [ {name, type, pk, fk} ]}}. Cached after the first call."""
    conn = psycopg2.connect(settings.sample_db_url)
    try:
        cur = conn.cursor()
        cur.execute(COLUMNS_SQL)
        tables: dict[str, list[dict]] = {}
        for table, column, data_type in cur.fetchall():
            tables.setdefault(table, []).append(
                {"name": column, "type": _TYPE_NAMES.get(data_type, data_type), "pk": False, "fk": None}
            )

        try:
            cur.execute(KEYS_SQL)
            for table, column, kind, ref_table, ref_column in cur.fetchall():
                for col in tables.get(table, []):
                    if col["name"] == column:
                        if kind == "p":
                            col["pk"] = True
                        elif kind == "f":
                            col["fk"] = f"{ref_table}.{ref_column}"
        except psycopg2.Error as exc:  # keys are helpful but not essential
            conn.rollback()
            log.warning("Could not read primary/foreign keys: %s", exc)
    finally:
        conn.close()
    return {"tables": tables}


def refresh_schema() -> None:
    get_schema.cache_clear()


def schema_to_text(schema: dict) -> str:
    """Compact text version of the schema that is sent to the LLM."""
    lines = []
    for table, columns in schema["tables"].items():
        parts = []
        for col in columns:
            piece = f"{col['name']} {col['type']}"
            if col["pk"]:
                piece += " PK"
            if col["fk"]:
                piece += f" -> {col['fk']}"
            parts.append(piece)
        lines.append(f"{table}({', '.join(parts)})")
    return "\n".join(lines)


def schema_for_ui(schema: dict) -> list[dict]:
    return [{"name": t, "columns": cols} for t, cols in schema["tables"].items()]


def select_tables(schema: dict, tables: list[str] | None) -> dict:
    """Return only explicitly selected existing tables; empty means all tables."""
    if not tables:
        return schema
    selected = set(tables)
    return {"tables": {name: cols for name, cols in schema["tables"].items() if name in selected}}
