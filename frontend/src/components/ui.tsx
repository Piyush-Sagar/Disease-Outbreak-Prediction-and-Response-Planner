"use client";

import type { ReactNode } from "react";
import { riskColor, severityColor } from "@/lib/format";
import type { RiskCategory, SeverityBand } from "@/lib/types";

export function Card({
  children,
  title,
  subtitle,
  className = "",
}: {
  children: ReactNode;
  title?: string;
  subtitle?: string;
  className?: string;
}) {
  return (
    <div className={`rounded-xl border border-slate-200 bg-white shadow-sm ${className}`}>
      {title && (
        <div className="border-b border-slate-100 px-4 py-3">
          <h2 className="text-sm font-semibold text-slate-800">{title}</h2>
          {subtitle && <p className="mt-0.5 text-xs text-slate-500">{subtitle}</p>}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  );
}

export function Badge({ children, color }: { children: ReactNode; color: string }) {
  return (
    <span
      className="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold text-white"
      style={{ backgroundColor: color }}
    >
      {children}
    </span>
  );
}

export function RiskBadge({ category }: { category: RiskCategory }) {
  return <Badge color={riskColor(category)}>{category}</Badge>;
}

export function SeverityBadge({ band }: { band: SeverityBand }) {
  return <Badge color={severityColor(band)}>{band}</Badge>;
}

export function MetricCard({
  label,
  value,
  color = "text-slate-900",
  hint,
}: {
  label: string;
  value: ReactNode;
  color?: string;
  hint?: string;
}) {
  return (
    <Card className="px-4 py-4">
      <p className="text-xs font-medium uppercase tracking-wide text-slate-500">{label}</p>
      <p className={`mt-1 text-2xl font-bold ${color}`}>{value}</p>
      {hint && <p className="mt-0.5 text-xs text-slate-400">{hint}</p>}
    </Card>
  );
}

export function RiskBar({ probability }: { probability: number }) {
  const pct = Math.max(0, Math.min(100, probability * 100));
  const color = riskColor(
    pct < 30 ? "Low" : pct < 50 ? "Moderate" : pct < 70 ? "High" : "Very High",
  );
  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full rounded-full" style={{ width: `${pct}%`, backgroundColor: color }} />
      </div>
      <span className="w-12 text-right text-xs font-semibold tabular-nums text-slate-600">
        {pct.toFixed(0)}%
      </span>
    </div>
  );
}

export function Spinner() {
  return (
    <div className="flex items-center justify-center py-12">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-slate-300 border-t-emerald-600" />
    </div>
  );
}

export function ErrorState({ message }: { message: string }) {
  return (
    <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-6 text-center">
      <p className="text-sm font-medium text-red-700">Unable to load data</p>
      <p className="mt-1 text-xs text-red-500">{message}</p>
    </div>
  );
}

export function DisclaimerBadge({ text = "DEMO DATA" }: { text?: string }) {
  return (
    <span className="inline-flex items-center rounded-md bg-amber-100 px-2 py-1 text-[10px] font-bold uppercase tracking-wide text-amber-800">
      {text}
    </span>
  );
}

export function InfoPanel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-lg border border-slate-200 bg-slate-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">{title}</p>
      <div className="mt-2 space-y-2 text-sm text-slate-600">{children}</div>
    </div>
  );
}

export function StatLine({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-4 py-1">
      <span className="text-xs text-slate-500">{label}</span>
      <span className="text-xs font-semibold text-slate-700">{value}</span>
    </div>
  );
}