export default function Sidebar({ schema, history, onPickHistory }) {
  return (
    <aside className="sidebar">
      <section className="card">
        <div className="section-heading">
          <h3>History</h3>
          {history.length > 0 && <span className="count">{history.length}</span>}
        </div>
        {history.length === 0 && <p className="hint">Your questions will appear here.</p>}
        <ul className="history">
          {history.map((h) => (
            <li key={h.id}>
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
            </li>
          ))}
        </ul>
      </section>

      <section className="card">
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
