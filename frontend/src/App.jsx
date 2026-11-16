import { useCallback, useEffect, useMemo, useState } from "react";
import { askQuestion, getHealth, getHistory, getSchema, runSql } from "./api.js";
import { inferChart } from "./chart.js";
import QuestionBox from "./components/QuestionBox.jsx";
import ResultChart from "./components/ResultChart.jsx";
import ResultTable from "./components/ResultTable.jsx";
import Sidebar from "./components/Sidebar.jsx";
import SqlViewer from "./components/SqlViewer.jsx";

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
  }, [loadHistory]);

  const chart = useMemo(
    () => (result && result.success ? inferChart(result.columns, result.rows) : null),
    [result]
  );

  function show(data) {
    setResult(data);
    setView(data.success && inferChart(data.columns, data.rows) ? "chart" : "table");
  }

  async function handleAsk(text) {
    if (text.trim().length < 3) return;
    setLoading(true);
    setError("");
    try {
      show(await askQuestion(text.trim()));
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
      </header>

      <div className="layout">
        <main className="main">
          <section className="welcome">
            <p className="eyebrow">Ask your data</p>
            <h2>Turn questions into answers.</h2>
            <p>Explore your PostgreSQL data with safe, editable SQL and instant visual summaries.</p>
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
            <section className="card">
              {result.success ? (
                <>
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

        <Sidebar schema={schema} history={history} onPickHistory={pickHistory} />
      </div>
    </div>
  );
}
