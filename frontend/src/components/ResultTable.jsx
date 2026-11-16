function formatCell(value) {
  if (value === null || value === undefined) return "—";
  if (typeof value === "number") return value.toLocaleString(undefined, { maximumFractionDigits: 2 });
  return String(value);
}

export default function ResultTable({ columns, rows }) {
  if (!rows.length) return <p className="hint">The query ran but returned no rows.</p>;

  const MAX_SHOWN = 200;
  const shown = rows.slice(0, MAX_SHOWN);

  return (
    <div className="table-wrap">
      <table>
        <thead>
          <tr>
            {columns.map((c, i) => (
              <th key={`${c}-${i}`}>{c}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {shown.map((row, r) => (
            <tr key={r}>
              {row.map((cell, c) => (
                <td key={c} className={typeof cell === "number" ? "num" : ""}>
                  {formatCell(cell)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
      {rows.length > MAX_SHOWN && (
        <p className="hint">Showing the first {MAX_SHOWN} of {rows.length} rows.</p>
      )}
    </div>
  );
}
