"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = ["#101A8A", "#F58220", "#2F6FED", "#16A34A", "#7C3AED"];

type Props = {
  chartType: "line" | "bar" | "pie" | "scatter";
  title?: string;
  labels: string[];
  values: number[];
  source?: string;
  caption?: string;
};

export function ArticleChart({ chartType, title, labels, values, source, caption }: Props) {
  const data = labels.map((label, index) => ({ label, value: values[index] ?? 0 }));

  return (
    <figure className="my-10">
      {title ? <p className="mb-3 text-center text-sm font-medium">{title}</p> : null}
      <div className="h-64 w-full min-w-0">
        <ResponsiveContainer width="100%" height="100%">
          {chartType === "line" ? (
            <LineChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#F58220" strokeWidth={2} dot={false} />
            </LineChart>
          ) : chartType === "pie" ? (
            <PieChart>
              <Pie data={data} dataKey="value" nameKey="label" outerRadius={90}>
                {data.map((entry, index) => (
                  <Cell key={entry.label} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          ) : chartType === "scatter" ? (
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis dataKey="value" tick={{ fontSize: 12 }} />
              <Tooltip />
              <Scatter data={data} fill="#101A8A" />
            </ScatterChart>
          ) : (
            <BarChart data={data}>
              <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
              <XAxis dataKey="label" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="value" fill="#101A8A" radius={[4, 4, 0, 0]} />
            </BarChart>
          )}
        </ResponsiveContainer>
      </div>
      {caption || source ? (
        <figcaption className="mt-3 text-center text-sm text-muted-foreground">
          {caption}
          {caption && source ? " · " : null}
          {source ? <span>Source: {source}</span> : null}
        </figcaption>
      ) : null}
    </figure>
  );
}
