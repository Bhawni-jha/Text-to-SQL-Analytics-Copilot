-- App database: stores the history of questions.
-- Run once:
--   psql -U postgres -c "CREATE DATABASE copilot_app;"
--   psql -U postgres -d copilot_app -f database/02_history_table.sql
-- (The backend also creates this table on startup if it is missing.)

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
);

CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history (created_at DESC);
