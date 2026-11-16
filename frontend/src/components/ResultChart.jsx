import { useState } from "react";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#2f6fed", "#e8572a", "#16a085", "#8e44ad", "#f39c12", "#34495e"];

export default function ResultChart({ chart }) {
  const [kind, setKind] = useState(chart.defaultKind);
  const Chart = kind === "line" ? LineChart : BarChart;

  return (
    <div>
      <div className="row">
        <button type="button" className={`btn small ${kind === "bar" ? "primary" : ""}`} onClick={() => setKind("bar")}>
          Bar
        </button>
        <button type="button" className={`btn small ${kind === "line" ? "primary" : ""}`} onClick={() => setKind("line")}>
          Line
        </button>
      </div>
      <div className="chart-box">
        <ResponsiveContainer width="100%" height="100%">
          <Chart data={chart.data} margin={{ top: 10, right: 20, left: 0, bottom: 30 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e3e6ef" />
            <XAxis dataKey={chart.xKey} interval={0} angle={-30} textAnchor="end" height={70} tick={{ fontSize: 12 }} />
            <YAxis tick={{ fontSize: 12 }} />
            <Tooltip />
            {chart.yKeys.length > 1 && <Legend />}
            {chart.yKeys.map((key, i) =>
              kind === "line" ? (
                <Line key={key} type="monotone" dataKey={key} stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
              ) : (
                <Bar key={key} dataKey={key} fill={COLORS[i % COLORS.length]} radius={[4, 4, 0, 0]} />
              )
            )}
          </Chart>
        </ResponsiveContainer>
      </div>
      {chart.clipped && <p className="hint">The chart shows the first 50 rows.</p>}
    </div>
  );
}
