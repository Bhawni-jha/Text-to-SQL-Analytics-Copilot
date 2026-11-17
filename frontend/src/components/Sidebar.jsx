import { useState } from "react";

export default function Sidebar({
  schema,
  history,
  onPickHistory,
  selectedTables,
  onToggleTable,
  dashboards,
  onLoadDashboard,
  onDeleteDashboard,
  onTestConnection,
  onDeleteHistory,
  onClearHistory,
  variant = "right",
}) {
  const [connectionUrl, setConnectionUrl] = useState("");
  const [connectionState, setConnectionState] = useState("");

  async function testConnection(event) {
    event.preventDefault();
    setConnectionState("Testing…");
    try {
      const result = await onTestConnection(connectionUrl);
      setConnectionState(result.ok ? `Connected to ${result.database}` : result.error);
    } catch (e) {
      setConnectionState(e.message);
    }
  }

  return (
    <aside className={`sidebar sidebar-${variant}`}>
      <section className="card connection-card left-only">
        <div className="section-heading">
          <div>
            <h3>Connect a database</h3>
            <p className="section-subtitle">Test a PostgreSQL source</p>
          </div>
        </div>
        <form className="connection-form" onSubmit={testConnection}>
          <input
            type="url"
            value={connectionUrl}
            onChange={(e) => setConnectionUrl(e.target.value)}
            placeholder="postgresql://user:pass@host/db"
            required
          />
          <button type="submit" className="btn small" disabled={!connectionUrl.trim()}>Test connection</button>
        </form>
        {connectionState && <p className="connection-state">{connectionState}</p>}
        <p className="hint compact-hint">Credentials are tested, not saved.</p>
      </section>
      <section className="card data-scope-card left-only">
        <div className="section-heading">
          <div>
            <h3>Data scope</h3>
            <p className="section-subtitle">Choose tables for the next answer</p>
          </div>
          <span className="count">{selectedTables.length || "All"}</span>
        </div>
        <div className="table-picker">
          {schema.map((t) => (
            <label key={t.name} className="table-option">
              <input
                type="checkbox"
                checked={selectedTables.length === 0 || selectedTables.includes(t.name)}
                onChange={() => onToggleTable(t.name)}
              />
              <span>{t.name}</span>
            </label>
          ))}
        </div>
        <p className="hint compact-hint">Leave all unchecked to use the full schema.</p>
      </section>
      <section className="card history-card right-only">
        <div className="section-heading">
          <div>
            <h3>History</h3>
            {history.length > 0 && <span className="count">{history.length}</span>}
          </div>
          {history.length > 0 && (
            <button type="button" className="clear-history" onClick={onClearHistory}>
              Clear all
            </button>
          )}
        </div>
        {history.length === 0 && <p className="hint">Your questions will appear here.</p>}
        <ul className="history">
          {history.map((h) => (
            <li key={h.id}>
              <div className="history-row">
                <button
                  type="button"
                  className="history-item"
                  onClick={() => onPickHistory(h.question)}
                  disabled={h.question === "(edited SQL)"}
                  title={h.sql || ""}
                >
                  <span className={h.success ? "dot ok" : "dot bad"} />
                  <span>{h.question}</span>
                </button>
                <button type="button" className="delete-history" onClick={() => onDeleteHistory(h.id)} aria-label={`Delete ${h.question}`}>
                  ×
                </button>
              </div>
            </li>
          ))}
        </ul>
      </section>

      {dashboards.length > 0 && (
        <section className="card saved-card right-only">
          <div className="section-heading">
            <div>
              <h3>Saved views</h3>
              <p className="section-subtitle">Your reusable questions</p>
            </div>
            <span className="count">{dashboards.length}</span>
          </div>
          <ul className="dashboard-list">
            {dashboards.map((dashboard) => (
              <li key={dashboard.id}>
                <button type="button" className="dashboard-item" onClick={() => onLoadDashboard(dashboard)}>
                  <strong>{dashboard.name}</strong>
                  <span>{dashboard.question}</span>
                </button>
                <button type="button" className="delete-dashboard" onClick={() => onDeleteDashboard(dashboard.id)} aria-label={`Delete ${dashboard.name}`}>×</button>
              </li>
            ))}
          </ul>
        </section>
      )}

      <section className="card tables-card left-only">
        <div className="section-heading">
          <h3>Tables</h3>
          {schema.length > 0 && <span className="count">{schema.length}</span>}
        </div>
        {schema.length === 0 && <p className="hint">Loading schema…</p>}
        {schema.map((t) => (
          <details key={t.name}>
            <summary>{t.name}</summary>
            <ul className="columns">
              {t.columns.map((c) => (
                <li key={c.name}>
                  <code>{c.name}</code> <span className="type">{c.type}</span>
                  {c.pk && <span className="tag">PK</span>}
                  {c.fk && <span className="tag">FK</span>}
                </li>
              ))}
            </ul>
          </details>
        ))}
      </section>
    </aside>
  );
}
