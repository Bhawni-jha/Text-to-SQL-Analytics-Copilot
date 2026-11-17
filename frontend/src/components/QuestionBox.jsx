const EXAMPLES = [
  "How many customers are in each country?",
  "Show the top 5 customers by total order value",
  "What is the total revenue for each product category?",
  "Show the number of orders in each month of 1997",
];

export default function QuestionBox({ value, onChange, onSubmit, loading }) {
  function handleKeyDown(e) {
    if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
      e.preventDefault();
      onSubmit(value);
    }
  }

  return (
    <section className="card question-card">
      <label className="label" htmlFor="question">
        Ask a question about your data
      </label>
      <textarea
        id="question"
        rows={2}
        value={value}
        placeholder="For example: Which employee handled the most orders?"
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        disabled={loading}
      />
      <div className="question-actions">
        <div className="chips">
          {EXAMPLES.map((ex) => (
            <button key={ex} type="button" className="chip" onClick={() => onChange(ex)} disabled={loading}>
              {ex}
            </button>
          ))}
        </div>
        <button
          type="button"
          className="btn primary"
          onClick={() => onSubmit(value)}
          disabled={loading || value.trim().length < 3}
        >
          {loading ? "Thinking…" : "Ask question"}
        </button>
      </div>
      <div className="question-footer">
        <p className="hint">Press <kbd>Ctrl</kbd> + <kbd>Enter</kbd> to send</p>
        <span className="secure-note"><span className="secure-dot" /> Read-only queries</span>
      </div>
    </section>
  );
}
