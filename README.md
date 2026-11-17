# Text-to-SQL Analytics Copilot

Ask a question in plain English. The app writes a SQL query, checks it is safe, runs it on
PostgreSQL (Northwind sample data) and shows the SQL, a table and a chart.

```
React (Vite)  ->  FastAPI  ->  Groq (writes SQL)
                     |-> SQL validator (sqlglot: one read-only SELECT only)
                     |-> Runner (read-only user, read-only transaction, 10 s timeout, row limit)
                     |-> retry once with the error message if the query fails
PostgreSQL: northwind (sample data)  +  copilot_app (question history)
```

## Folder structure

```
Text-to-SQL/
  .vscode/            VS Code settings, debug config, tasks
  database/
    01_readonly_user.sql    read-only role for the backend
    02_history_table.sql    history table (backend also creates it)
  backend/
    app/
      config.py      settings from .env
      schema.py      reads tables, columns, keys
      llm.py         prompt + Groq call
      validator.py   safety checks on the SQL
      runner.py      safe query execution
      history.py     saves/list past questions
      service.py     question -> SQL -> validate -> run -> retry
      models.py      request/response models
      main.py        FastAPI endpoints
    tests/
      eval_set.json      15 questions with correct SQL
      run_eval.py        measures accuracy
      test_validator.py  checks the safety validator
    requirements.txt
    .env.example
  frontend/
    src/  App.jsx, api.js, chart.js, styles.css, components/
    package.json, vite.config.js, index.html
```

## Setup (Windows, VS Code, PowerShell)

1. Install: Python 3.10+, Node.js LTS, PostgreSQL (with the `northwind` database loaded).
2. Database users and tables (from the project root):
   ```powershell
   # edit the password inside database\01_readonly_user.sql first
   psql -U postgres -d northwind -f database\01_readonly_user.sql
   psql -U postgres -c "CREATE DATABASE copilot_app;"
   psql -U postgres -d copilot_app -f database\02_history_table.sql
   ```
3. Backend:
   ```powershell
   cd backend
   python -m venv .venv          # skip if .venv already exists
   .venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   copy .env.example .env        # then edit .env
   uvicorn app.main:app --reload --port 8000
   ```
   Open http://127.0.0.1:8000/docs to test the API.
4. Frontend (new terminal):
   ```powershell
   cd frontend
   npm install
   npm run dev
   ```
   Open http://localhost:5173

## Test and measure

```powershell
cd backend
python tests/test_validator.py   # safety checks
python tests/run_eval.py         # accuracy on 15 questions
```

## Included workflows
- `tests/eval_set.json` contains 30 evaluation questions. Run `python tests/run_eval.py` to measure accuracy and inspect `tests/eval_results.json`.
- Select a smaller set of tables in the **Data scope** panel before asking a question. This sends less schema context to the model.
- Create a local account from the **Sign in** menu to keep history separate and save reusable dashboard questions.
- Use **Connect a database** to test a PostgreSQL URL. Credentials are tested for the request and are not stored.

For local authentication, add a long random `AUTH_SECRET` to `backend/.env`; the default development value must not be used in production.
