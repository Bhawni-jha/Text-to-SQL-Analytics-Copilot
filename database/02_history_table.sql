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
    ,user_id    INTEGER
);

CREATE INDEX IF NOT EXISTS idx_query_history_created_at ON query_history (created_at DESC);

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY, email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS saved_dashboards (
    id SERIAL PRIMARY KEY, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL, question TEXT NOT NULL DEFAULT '', sql TEXT NOT NULL DEFAULT '',
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS idx_query_history_user ON query_history(user_id, created_at DESC);
