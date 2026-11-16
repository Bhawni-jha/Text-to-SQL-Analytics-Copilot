// Decides whether a result can be drawn as a chart.
// Rule: the first column is the label (x axis) and every later column that is
// fully numeric becomes a data series.
export function inferChart(columns, rows) {
  if (!rows || rows.length < 2 || columns.length < 2) return null;

  const isNum = (v) => typeof v === "number" && Number.isFinite(v);
  const numericIdx = [];
  for (let i = 1; i < columns.length; i++) {
    if (rows.every((r) => r[i] === null || isNum(r[i]))) numericIdx.push(i);
  }
  if (numericIdx.length === 0) return null;

  const first = rows[0][0];
  const looksLikeTime =
    /date|month|year|day|week|quarter|time/i.test(columns[0]) ||
    /^\d{4}-\d{2}/.test(String(first));

  const shown = rows.slice(0, 50);
  const data = shown.map((r) => {
    const item = { [columns[0]]: r[0] === null ? "—" : String(r[0]) };
    numericIdx.forEach((i) => {
      item[columns[i]] = r[i];
    });
    return item;
  });

  return {
    xKey: columns[0],
    yKeys: numericIdx.map((i) => columns[i]),
    defaultKind: looksLikeTime ? "line" : "bar",
    data,
    clipped: rows.length > shown.length,
  };
}
