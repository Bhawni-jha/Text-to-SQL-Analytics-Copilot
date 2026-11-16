import { useEffect, useState } from "react";

export default function SqlViewer({ sql, onRun, running }) {
  const [draft, setDraft] = useState(sql || "");
  const [copied, setCopied] = useState(false);

  // When a new query arrives, replace whatever the user was editing
  useEffect(() => {
    setDraft(sql || "");
  }, [sql]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(draft);
      setCopied(true);
      setTimeout(() => setCopied(false), 1500);
    } catch {
      // clipboard blocked: ignore
    }
  }

  const changed = draft.trim() !== (sql || "").trim();

  return (
    <div className="sql-box">
      <div className="row between">
        <span className="label">Generated SQL</span>
        <div className="row">
          <button type="button" className="btn small" onClick={copy}>
            {copied ? "Copied" : "Copy"}
          </button>
          <button
            type="button"
            className="btn small primary"
            onClick={() => onRun(draft)}
            disabled={running || !changed}
            title={changed ? "Run your edited query" : "Edit the SQL to enable this"}
          >
            {running ? "Running…" : "Run edited SQL"}
          </button>
        </div>
      </div>
      <textarea
        className="code"
        spellCheck={false}
        rows={Math.min(14, Math.max(4, draft.split("\n").length + 1))}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
      />
    </div>
  );
}
