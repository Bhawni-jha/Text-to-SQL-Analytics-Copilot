import { useCallback, useEffect, useMemo, useState } from "react";
import {
  askQuestion,
  clearHistory,
  deleteHistory,
  deleteDashboard,
  getCurrentUser,
  getDashboards,
  getHealth,
  getHistory,
  getSchema,
  login,
  register,
  runSql,
  saveDashboard,
  setAuthToken,
  testConnection,
} from "./api.js";
import { inferChart } from "./chart.js";
import QuestionBox from "./components/QuestionBox.jsx";
import ResultChart from "./components/ResultChart.jsx";
import ResultTable from "./components/ResultTable.jsx";
import Sidebar from "./components/Sidebar.jsx";
import SqlViewer from "./components/SqlViewer.jsx";
import AuthPanel from "./components/AuthPanel.jsx";

export default function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [history, setHistory] = useState([]);
  const [schema, setSchema] = useState([]);
  const [view, setView] = useState("table");
  const [health, setHealth] = useState("checking");
  const [selectedTables, setSelectedTables] = useState([]);
  const [user, setUser] = useState(null);
  const [dashboards, setDashboards] = useState([]);

  const loadHistory = useCallback(() => {
    getHistory()
      .then((data) => setHistory(data.items))
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadHistory();
    getHealth()
      .then(() => setHealth("online"))
      .catch(() => setHealth("offline"));
    getSchema()
      .then((data) => setSchema(data.tables))
      .catch((e) => setError(e.message));
    getCurrentUser()
      .then((data) => setUser(data))
      .catch(() => {});
  }, [loadHistory]);

  useEffect(() => {
    if (!user) {
      setDashboards([]);
      return;
    }
    getDashboards().then(setDashboards).catch(() => {});
  }, [user]);

  const chart = useMemo(
    () => (result && result.success ? inferChart(result.columns, result.rows) : null),
    [result]
  );

  function show(data) {
    setResult(data);
    setView(data.success && inferChart(data.columns, data.rows) ? "chart" : "table");
  }

  async function handleAsk(text, tables = selectedTables) {
    if (text.trim().length < 3) return;
    setLoading(true);
    setError("");
    try {
      show(await askQuestion(text.trim(), tables));
      loadHistory();
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  async function handleRun(sql) {
    setRunning(true);
    setError("");
    try {
      show(await runSql(sql));
      loadHistory();
    } catch (e) {
      setError(e.message);
    } finally {
      setRunning(false);
    }
  }

  function pickHistory(text) {
    setQuestion(text);
    handleAsk(text);
  }

  function toggleTable(table) {
    setSelectedTables((current) => {
      const active = current.length === 0 ? schema.map((item) => item.name) : current;
      const next = active.includes(table)
        ? active.filter((item) => item !== table)
        : [...active, table];
      return next.length === schema.length ? [] : next;
    });
  }

  async function handleAuth(mode, email, password) {
    const data = mode === "login"
      ? await login(email, password)
      : await register(email, password);
    setAuthToken(data.token);
    setUser({ id: data.user_id, email: data.email });
    loadHistory();
  }

  function handleLogout() {
    setAuthToken("");
    setUser(null);
    setDashboards([]);
  }

  async function handleSaveDashboard() {
    if (!user || !result?.success) return;
    const title = window.prompt("Name this saved view", question.slice(0, 60) || "Saved query");
    if (!title?.trim()) return;
    try {
      const saved = await saveDashboard({
        name: title.trim(),
        question,
        sql: result.sql,
        config: { tables: selectedTables },
      });
      setDashboards((current) => [{
        id: saved.id,
        name: title.trim(),
        question,
        sql: result.sql,
        config: { tables: selectedTables },
      }, ...current]);
    } catch (e) {
      setError(e.message);
    }
  }

  function loadDashboard(dashboard) {
    setQuestion(dashboard.question);
    const tables = dashboard.config?.tables || [];
    setSelectedTables(tables);
    handleAsk(dashboard.question, tables);
  }

  async function handleDeleteDashboard(id) {
    try {
      await deleteDashboard(id);
      setDashboards((current) => current.filter((dashboard) => dashboard.id !== id));
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleTestConnection(url) {
    const result = await testConnection(url);
    if (!result.ok) throw new Error(result.error || "Connection failed");
    return result;
  }

  async function handleDeleteHistory(id) {
    try {
      await deleteHistory(id);
      setHistory((current) => current.filter((item) => item.id !== id));
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleClearHistory() {
    if (!window.confirm("Delete all query history? This cannot be undone.")) return;
    try {
      await clearHistory();
      setHistory([]);
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">TS</div>
          <div>
            <p className="eyebrow">Analytics workspace</p>
            <h1>Text-to-SQL Copilot</h1>
          </div>
        </div>
        <div className={`status status-${health}`}>
          <span className="status-dot" />
          {health === "checking" ? "Connecting" : health === "online" ? "API online" : "API offline"}
        </div>
        <AuthPanel user={user} onAuth={handleAuth} onLogout={handleLogout} />
      </header>

      <div className="layout">
        <Sidebar
          variant="left"
          schema={schema}
          history={history}
          onPickHistory={pickHistory}
          selectedTables={selectedTables}
          onToggleTable={toggleTable}
          dashboards={dashboards}
          onLoadDashboard={loadDashboard}
          onDeleteDashboard={handleDeleteDashboard}
          onTestConnection={handleTestConnection}
          onDeleteHistory={handleDeleteHistory}
          onClearHistory={handleClearHistory}
        />
        <main className="main">
          <section className="workspace-intro">
            <div className="intro-copy">
              <p className="eyebrow">Ask your data</p>
              <h2>Make your data speak.</h2>
              <p>Ask in plain English. Get safe SQL, a clear answer, and a visual summary.</p>
            </div>
            <div className="intro-stats" aria-label="Workspace details">
              <div className="intro-stat">
                <strong>{schema.length || "—"}</strong>
                <span>tables</span>
              </div>
              <div className="intro-stat">
                <strong>{history.length || "0"}</strong>
                <span>queries</span>
              </div>
            </div>
          </section>
          <QuestionBox value={question} onChange={setQuestion} onSubmit={handleAsk} loading={loading} />

          {error && <div className="alert">{error}</div>}

          {!result && !loading && (
            <section className="empty-state card">
              <div className="empty-icon">✦</div>
              <h3>Your next insight starts here</h3>
              <p>Ask a question above or choose one of the examples to explore your Northwind data.</p>
            </section>
          )}

          {loading && (
            <section className="loading-state card">
              <span className="spinner" />
              <div>
                <strong>Building your answer</strong>
                <p className="hint">Inspecting the schema and writing a safe query…</p>
              </div>
            </section>
          )}

          {result && (
            <section className="card result-card">
              {result.success ? (
                <>
                  <div className="result-heading">
                    <div>
                      <p className="eyebrow">Query result</p>
                      <h3>Here is what I found</h3>
                    </div>
                    <div className="result-actions">
                      {user && <button type="button" className="btn small" onClick={handleSaveDashboard}>Save view</button>}
                      <span className="result-badge">Complete</span>
                    </div>
                  </div>
                  {result.explanation && <p className="explain">{result.explanation}</p>}
                  <p className="meta">
                    {result.row_count} row{result.row_count === 1 ? "" : "s"}
                    {result.truncated && " (limit reached, more rows exist)"} · {result.elapsed_ms} ms
                    {result.attempts > 1 && " · fixed itself after an error"}
                  </p>
                </>
              ) : (
                <div className="alert">
                  <strong>Could not answer this question.</strong>
                  <p>{result.error}</p>
                </div>
              )}

              {result.sql && <SqlViewer sql={result.sql} onRun={handleRun} running={running} />}

              {result.success && (
                <>
                  <div className="row tabs">
                    <button type="button" className={`btn small ${view === "table" ? "primary" : ""}`} onClick={() => setView("table")}>
                      Table
                    </button>
                    {chart && (
                      <button type="button" className={`btn small ${view === "chart" ? "primary" : ""}`} onClick={() => setView("chart")}>
                        Chart
                      </button>
                    )}
                  </div>
                  {view === "chart" && chart ? (
                    <ResultChart key={result.history_id ?? result.sql} chart={chart} />
                  ) : (
                    <ResultTable columns={result.columns} rows={result.rows} />
                  )}
                </>
              )}
            </section>
          )}
        </main>

        <Sidebar
          variant="right"
          schema={schema}
          history={history}
          onPickHistory={pickHistory}
          selectedTables={selectedTables}
          onToggleTable={toggleTable}
          dashboards={dashboards}
          onLoadDashboard={loadDashboard}
          onDeleteDashboard={handleDeleteDashboard}
          onTestConnection={handleTestConnection}
          onDeleteHistory={handleDeleteHistory}
          onClearHistory={handleClearHistory}
        />
      </div>
    </div>
  );
}
