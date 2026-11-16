-- Read-only user used by the backend to run generated SQL.
-- Run once against the Northwind database:
--   psql -U postgres -d northwind -f database/01_readonly_user.sql
-- IMPORTANT: change the password below and use the same one in backend/.env

DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'myapp') THEN
        CREATE ROLE myapp LOGIN PASSWORD 'postgress';
    ELSE
        ALTER ROLE myapp WITH PASSWORD 'postgress';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE northwind TO myapp;
GRANT USAGE ON SCHEMA public TO myapp;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO myapp;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO myapp;

-- Extra safety on the database side (the backend also enforces these)
ALTER ROLE myapp SET statement_timeout = '10s';
ALTER ROLE myapp SET default_transaction_read_only = on;
