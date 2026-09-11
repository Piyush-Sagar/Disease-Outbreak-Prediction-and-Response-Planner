"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { fmtDate } from "@/lib/format";
import type { CasePoint, PriorityRow } from "@/lib/types";

export function CasesLineChart({
  data,
  height = 260,
}: {
  data: CasePoint[];
  height?: number;
}) {
  const rows = data.map((d) => ({ ...d, date: fmtDate(d.date) }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <LineChart data={rows} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
        <XAxis dataKey="date" tick={{ fontSize: 10 }} minTickGap={32} />
        <YAxis
          tick={{ fontSize: 10 }}
          width={44}
          tickFormatter={(v: number) => v.toLocaleString("en-IN")}
        />
        <Tooltip formatter={(v) => Number(v).toLocaleString("en-IN")} />
        <Line
          type="monotone"
          dataKey="total_cases"
          name="Weekly cases"
          stroke="#059669"
          strokeWidth={2}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="total_deaths"
          name="Deaths"
          stroke="#dc2626"
          strokeWidth={1.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

const BAR_COLORS = ["#16a34a", "#eab308", "#f97316", "#dc2626"];

export function RiskByRegionChart({
  data,
  height = 320,
}: {
  data: PriorityRow[];
  height?: number;
}) {
  const rows = data
    .slice()
    .sort((a, b) => b.outbreak_probability - a.outbreak_probability)
    .map((d) => ({
      name: d.name,
      risk: Math.round(d.outbreak_probability * 100),
      priority: d.priority_score,
    }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} margin={{ top: 8, right: 12, bottom: 4, left: 0 }}>
        <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" />
        <XAxis dataKey="name" tick={{ fontSize: 10 }} interval={0} angle={-35} textAnchor="end" />
        <YAxis domain={[0, 100]} tick={{ fontSize: 10 }} width={34} />
        <Tooltip />
        <Bar dataKey="risk" name="Predicted risk (%)" radius={[3, 3, 0, 0]}>
          {rows.map((row) => (
            <Cell key={row.name} fill={row.risk < 30 ? BAR_COLORS[0] : row.risk < 50 ? BAR_COLORS[1] : row.risk < 70 ? BAR_COLORS[2] : BAR_COLORS[3]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

export function FeatureImportanceChart({
  data,
  height = 260,
}: {
  data: { feature: string; importance: string }[];
  height?: number;
}) {
  const rows = data
    .slice()
    .sort((a, b) => Number(a.importance) - Number(b.importance))
    .map((d) => ({ feature: d.feature, importance: Number(d.importance) }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 24 }}>
        <CartesianGrid stroke="#e2e8f0" strokeDasharray="3 3" horizontal={false} />
        <XAxis type="number" tick={{ fontSize: 10 }} />
        <YAxis type="category" dataKey="feature" tick={{ fontSize: 10 }} width={44} />
        <Tooltip />
        <Bar dataKey="importance" fill="#0ea5e9" radius={[0, 3, 3, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}