# Text-to-SQL Analytics Copilot

## 1. What this project does

Text-to-SQL Analytics Copilot lets a person ask a database question in normal English.
For example:

> Show the top 5 customers by total order value.

The application then:

1. Reads the database schema.
2. Sends the question and relevant schema to Groq.
3. Receives a PostgreSQL `SELECT` query.
4. Validates that the query is read-only and safe.
5. Runs it with a read-only database user.
6. Displays the SQL, result table, and chart when appropriate.

It also includes table selection, query history, accounts, saved views, database connection testing,
and history deletion.

## 2. What the finished application looks like

![Text-to-SQL Analytics Copilot interface](./assets/project-screenshot.png)

The interface has:

- **Left panel:** database connection test, table scope, and schema details.
- **Center panel:** natural-language question box, generated SQL, table, and chart.
- **Right panel:** query history and saved views.
- **Top bar:** API status and sign-in controls.

## 3. Database overview

The project uses the Northwind sample PostgreSQL database. The main business tables are shown below.

![Northwind database schema](./assets/database-schema.svg)

The application also uses a separate application database for:

- user accounts,
- query history,
- saved dashboards/views.

The sample database is read-only for the backend. The application database is writable because
history and accounts must be stored.

## 4. Beginner vocabulary

| Term | Meaning |
|---|---|
| Database | An organized collection of information |
| Table | A spreadsheet-like group of related records |
| Column | One type of information in a table |
| Row | One record in a table |
| SQL | The language used to ask a database for information |
| PostgreSQL | The database software used by this project |
| API | A backend address that the frontend can call |
| Frontend | The web page a user interacts with |
| Backend | The server that validates requests and talks to databases |
| Schema | A description of tables, columns, and relationships |
| Primary key | A unique identifier for a row |
| Foreign key | A column that connects one table to another |

## 5. Project structure

```text
Text-to-SQL/
├── backend/
│   ├── app/
│   │   ├── main.py          API routes and application startup
│   │   ├── config.py        Environment-based configuration
│   │   ├── models.py        Request and response validation
│   │   ├── llm.py           Groq prompt and response parsing
│   │   ├── schema.py        Reads PostgreSQL table metadata
│   │   ├── service.py       Question → SQL → validation → execution flow
│   │   ├── validator.py     Blocks unsafe SQL
│   │   ├── runner.py        Runs safe SQL with limits and timeout
│   │   ├── history.py       Stores and deletes query history
│   │   ├── auth.py          Password hashing and signed sessions
│   │   └── dashboard.py     Saved-view persistence
│   ├── tests/
│   │   ├── eval_set.json     30 known questions and expected SQL
│   │   ├── run_eval.py       Accuracy evaluator
│   │   └── test_validator.py SQL safety checks
│   └── requirements.txt
├── database/
│   ├── 01_readonly_user.sql
│   └── 02_history_table.sql
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   ├── chart.js
│   │   ├── styles.css
│   │   └── components/
│   ├── package.json
│   └── vite.config.js
└── docs/
    ├── PROJECT_DOCUMENTATION.md
    └── assets/
```

## 6. How the application works

```mermaid
flowchart LR
    A[User asks question] --> B[React frontend]
    B --> C[FastAPI /api/ask]
    C --> D[Read selected schema]
    D --> E[Groq generates SQL]
    E --> F[sqlglot validates SELECT only]
    F --> G[Read-only PostgreSQL runner]
    G --> H[Table and chart response]
    C --> I[Save history]
```

### Step 1: The user asks a question

The question is typed into the React interface. The frontend sends JSON such as:

```json
{
  "question": "How many customers are in each country?",
  "tables": ["customers"]
}
```

The `tables` array is optional. An empty array means the full schema can be used.

### Step 2: The backend reads the schema

`backend/app/schema.py` reads table names, columns, data types, primary keys, and foreign keys
from PostgreSQL's metadata tables.

If the user selected only a few tables, the backend sends only those tables to the model. This
reduces prompt size and helps the model focus on the relevant data.

### Step 3: Groq generates SQL

`backend/app/llm.py` gives Groq:

- the database schema,
- the user's question,
- business definitions such as the revenue formula.

The model must return JSON containing one SQL query and a short explanation.

### Step 4: The query is validated

The validator allows one read-only `SELECT` query or a read-only `WITH` query. It blocks:

- `INSERT`
- `UPDATE`
- `DELETE`
- `DROP`
- `ALTER`
- `CREATE`
- multiple statements
- locking queries such as `FOR UPDATE`

### Step 5: The query runs safely

The runner:

- connects with the read-only sample database user,
- opens a read-only transaction,
- applies a statement timeout,
- applies a maximum row limit,
- converts PostgreSQL values to JSON-compatible values.

If a query fails, the service can retry with the database error so the model can correct its SQL.

### Step 6: The frontend presents the answer

The result includes:

- generated SQL,
- explanation,
- row count,
- execution time,
- a table,
- a chart when the result shape supports visualization.

## 7. Features

### Natural-language questions

Use the example chips or type your own question. Press `Ctrl + Enter` to submit.

### Data scope

Select only the tables needed for a question. Leave all tables selected to use the complete
schema.

### Generated SQL

The SQL is editable. After editing it, select **Run edited SQL**. The same safety validator is
used, so editing cannot bypass read-only protections.

### Charts

The app automatically detects useful chart shapes. Supported display options include bar and
line charts. Category colors use distinct hues so multiple series are easier to compare.

### History

Successful and failed questions are stored in the application database. History can be:

- opened again to rerun a question,
- deleted one item at a time,
- cleared with **Clear all**.

### Accounts

Users can create a local account with an email and password. Passwords are stored as PBKDF2
hashes, not plain text. Signed bearer sessions are stored in the browser.

### Saved views

After signing in, use **Save view** on a successful result. Saved views remember the question,
SQL, and selected table scope.

### Database connection testing

Signed-in users can test a PostgreSQL connection URL. The URL is used only for the test request
and is not saved by the application.

## 8. Installation requirements

Install the following:

1. Python 3.10 or newer
2. Node.js LTS
3. PostgreSQL
4. A Northwind PostgreSQL database
5. A Groq API key

Check installations:

```powershell
python --version
node --version
npm --version
psql --version
```

## 9. Database setup

Open PowerShell in the project root:

```powershell
cd C:\Users\user\Downloads\Text-to-SQL\Text-to-SQL
```

Create the read-only role on the sample database:

```powershell
psql -U postgres -d northwind -f database\01_readonly_user.sql
```

Create the application database:

```powershell
psql -U postgres -c "CREATE DATABASE myapp_db;"
psql -U postgres -d myapp_db -f database\02_history_table.sql
```

If the database already exists, do not run the `CREATE DATABASE` command again. The backend also
creates missing application tables during startup.

## 10. Environment configuration

Open [backend/.env](../backend/.env). Never commit this file or share its values publicly.

Example:

```env
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
SAMPLE_DB_URL=postgresql://copilot_ro:password@localhost:5432/northwind
APP_DB_URL=postgresql://postgres:password@localhost:5432/myapp_db
AUTH_SECRET=generate-a-long-random-secret
MAX_ROWS=1000
QUERY_TIMEOUT_SECONDS=10
MAX_ATTEMPTS=2
```

Generate `AUTH_SECRET` with:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the printed value after `AUTH_SECRET=`.

## 11. Run the backend

Open the first PowerShell terminal:

```powershell
cd C:\Users\user\Downloads\Text-to-SQL\Text-to-SQL\backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Backend addresses:

- API: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health check: http://127.0.0.1:8000/api/health

## 12. Run the frontend

Open a second PowerShell terminal:

```powershell
cd C:\Users\user\Downloads\Text-to-SQL\Text-to-SQL\frontend
npm install
npm run dev
```

Open http://localhost:5173.

The Vite development server forwards `/api` requests to the FastAPI server on port 8000.

## 13. API reference

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Check backend status |
| GET | `/api/schema` | Read available tables and columns |
| POST | `/api/ask` | Convert a question into SQL and run it |
| POST | `/api/run` | Validate and run edited SQL |
| GET | `/api/history` | List history |
| DELETE | `/api/history/{id}` | Delete one history item |
| DELETE | `/api/history` | Delete all current history |
| POST | `/api/auth/register` | Create an account |
| POST | `/api/auth/login` | Sign in |
| GET | `/api/auth/me` | Read the current account |
| GET | `/api/dashboards` | List saved views |
| POST | `/api/dashboards` | Save a view |
| PUT | `/api/dashboards/{id}` | Update a view |
| DELETE | `/api/dashboards/{id}` | Delete a view |
| POST | `/api/connections/test` | Test a PostgreSQL URL |

## 14. Testing

Run SQL safety tests:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
python tests\test_validator.py
```

Run the 30-question evaluation:

```powershell
python tests\run_eval.py
```

The evaluator compares generated results with the known correct SQL results and writes details
to `backend/tests/eval_results.json`. It requires a working database, Groq key, and backend
configuration.

Build the frontend:

```powershell
cd ..\frontend
npm run build
```

## 15. Common problems

### `python` is not recognized

Install Python and enable **Add Python to PATH** during installation.

### PowerShell blocks activation

Run PowerShell as your normal user and use:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then activate `.venv` again.

### API offline in the frontend

Confirm the backend terminal is running on port 8000:

```powershell
uvicorn app.main:app --reload --port 8000
```

### Database connection failed

Check:

- PostgreSQL service is running.
- `northwind` exists.
- usernames and passwords in `.env` are correct.
- `SAMPLE_DB_URL` points to the sample database.
- `APP_DB_URL` points to the application database.

### Groq authentication error

Check that `GROQ_API_KEY` is present and valid in `backend/.env`. Restart the backend after
editing `.env`.

### Tables are empty in the UI

The backend reads schema metadata from the sample database. Confirm that the backend can connect
to `SAMPLE_DB_URL` and that the database user can read `information_schema`.

## 16. Security notes

- Never commit `.env` files, API keys, database passwords, or `AUTH_SECRET`.
- Use a unique long `AUTH_SECRET` outside local development.
- Keep the sample database user read-only.
- Do not expose PostgreSQL directly to the public internet.
- The connection-test feature requires authentication and does not save credentials.
- Keep the SQL validator and read-only runner enabled in production.

## 17. How to extend the project

Good next improvements include:

- Add automated frontend tests.
- Add pagination for very large history lists.
- Add role-based access control.
- Add encrypted storage if database connections ever need to be saved.
- Add more evaluation questions and track accuracy after prompt changes.
- Add deployment configuration for a hosted PostgreSQL and FastAPI service.
