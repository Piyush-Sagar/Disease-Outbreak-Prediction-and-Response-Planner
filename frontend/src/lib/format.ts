import type { RiskCategory, SeverityBand } from "@/lib/types";

export const RISK_COLORS: Record<RiskCategory, string> = {
  Low: "#16a34a",
  Moderate: "#eab308",
  High: "#f97316",
  "Very High": "#dc2626",
};

export const SEVERITY_COLORS: Record<SeverityBand, string> = {
  LOW: "#16a34a",
  MODERATE: "#eab308",
  HIGH: "#f97316",
  CRITICAL: "#dc2626",
};

export function riskColor(category: RiskCategory): string {
  return RISK_COLORS[category] ?? "#6b7280";
}

export function riskCategory(probability: number, bands = DEFAULT_BANDS): RiskCategory {
  const pct = Math.max(0, Math.min(100, probability * 100));
  const match = bands.find((b) => pct >= b.min && pct <= b.max);
  return (match?.label as RiskCategory) ?? "Low";
}

export const DEFAULT_BANDS = [
  { label: "Low", min: 0, max: 29 },
  { label: "Moderate", min: 30, max: 49 },
  { label: "High", min: 50, max: 69 },
  { label: "Very High", min: 70, max: 100 },
];

export function severityColor(band: SeverityBand): string {
  return SEVERITY_COLORS[band] ?? "#6b7280";
}

export function fmtPct(probability: number): string {
  return `${(probability * 100).toFixed(1)}%`;
}

export function fmtInt(value: number | null | undefined): string {
  if (value == null) return "—";
  return value.toLocaleString("en-IN");
}

export function fmtDate(date: string): string {
  if (!date) return "—";
  const d = new Date(`${date}T00:00:00`);
  if (Number.isNaN(d.getTime())) return date;
  return d.toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" });
}